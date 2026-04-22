from __future__ import annotations

import math
import os
import shutil
import subprocess
import tarfile
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.core.http_errors import bad_request
from app.core.maintenance import enter_maintenance, leave_maintenance
from app.core.time import utcnow
from app.models.backup_record import BackupRecord
from app.schemas.backup_domain import BackupCreateResponse, BackupListItem, BackupListPage, BackupRestoreResponse


def _is_postgres(database_url: str) -> bool:
    return "postgresql" in database_url or "postgres" in database_url


def _is_sqlite(database_url: str) -> bool:
    return database_url.startswith("sqlite")


def _pg_tool_dsn(url: str) -> str:
    """pg_dump/psql expect postgresql:// not sqlalchemy dialect prefixes."""
    u = str(url)
    return u.replace("postgresql+psycopg2://", "postgresql://").replace("postgresql+asyncpg://", "postgresql://")


def _run_pg_dump(database_url: str, sql_out: Path) -> None:
    result = subprocess.run(
        ["pg_dump", "--format=plain", "--no-owner", "--dbname", database_url, "-f", str(sql_out)],
        capture_output=True,
        text=True,
        timeout=3600,
        check=False,
        env={**os.environ},
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "pg_dump failed")


def _run_psql_file(database_url: str, sql_path: Path) -> None:
    result = subprocess.run(
        ["psql", database_url, "-v", "ON_ERROR_STOP=1", "-f", str(sql_path)],
        capture_output=True,
        text=True,
        timeout=3600,
        check=False,
        env={**os.environ},
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "psql restore failed")


def _dump_sqlite_schema_data(session: Session, sql_out: Path) -> None:
    """Dump SQLite schema/data robustly across pooled/adapter connection wrappers."""
    import sqlite3

    bind = session.get_bind()
    raw = bind.raw_connection()
    try:
        source = getattr(raw, "dbapi_connection", None) or getattr(raw, "driver_connection", None) or raw
        if not hasattr(source, "iterdump"):
            # Some wrappers don't expose iterdump directly. Reopen by path when possible.
            db_path = source.execute("PRAGMA database_list").fetchone()[2]
            source = sqlite3.connect(db_path)
        with sql_out.open("w", encoding="utf-8") as f:
            for line in source.iterdump():
                f.write(f"{line}\n")
    finally:
        raw.close()


def _restore_sqlite_engine(engine: sa.Engine, sql_path: Path) -> None:
    script = sql_path.read_text(encoding="utf-8")
    from app.models.base import Base

    Base.metadata.drop_all(bind=engine)
    raw = engine.raw_connection()
    try:
        dbapi = getattr(raw, "dbapi_connection", None) or getattr(raw, "driver_connection", None) or raw
        if not hasattr(dbapi, "executescript"):
            raise RuntimeError("Cannot access SQLite connection for restore")
        dbapi.executescript("PRAGMA foreign_keys=OFF;")
        dbapi.executescript(script)
        dbapi.executescript("PRAGMA foreign_keys=ON;")
    finally:
        raw.close()


def _pack_backup_archive(sql_file: Path, upload_root: Path, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(dest, "w:gz") as tar:
        tar.add(sql_file, arcname="database.sql")
        if upload_root.exists() and any(upload_root.iterdir()):
            tar.add(upload_root, arcname="uploads")
    return dest.stat().st_size


def _extract_archive(archive: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        try:
            tar.extractall(path=dest_dir, filter="data")  # type: ignore[call-arg]
        except TypeError:
            tar.extractall(path=dest_dir)


def _sync_upload_tree(src: Path, upload_root: Path) -> None:
    if not src.exists():
        upload_root.mkdir(parents=True, exist_ok=True)
        return
    if upload_root.exists():
        shutil.rmtree(upload_root)
    shutil.copytree(src, upload_root)


class BackupService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _settings(self) -> Settings:
        return get_settings()

    def create_manual(self) -> BackupCreateResponse:
        settings = self._settings()
        bind_url = str(self.db.get_bind().url)
        database_url = bind_url
        backup_root = Path(settings.backup_root)
        backup_root.mkdir(parents=True, exist_ok=True)
        upload_root = Path(settings.upload_root)

        bid = uuid.uuid4()
        now = utcnow()
        record = BackupRecord(
            id=bid,
            backup_type="manual",
            backup_path="",
            size_bytes=0,
            status="failed",
            error_detail=None,
            created_at=now,
            restored_at=None,
        )
        self.db.add(record)
        # Persist first so low-level sqlite snapshot operations cannot invalidate this row.
        self.db.commit()
        self.db.refresh(record)

        staging = Path(tempfile.mkdtemp(prefix="backup_stage_"))
        sql_path = staging / "database.sql"
        artifact = backup_root / f"{bid}_manual_{now.strftime('%Y%m%d_%H%M%S')}.tar.gz"
        try:
            if _is_postgres(database_url):
                _run_pg_dump(_pg_tool_dsn(database_url), sql_path)
            elif _is_sqlite(database_url):
                _dump_sqlite_schema_data(self.db, sql_path)
            else:
                raise RuntimeError("Unsupported database URL for backup")

            size = _pack_backup_archive(sql_path, upload_root, artifact)
            record.backup_path = str(artifact.resolve())
            record.size_bytes = size
            record.status = "completed"
            self.db.commit()
            self.db.refresh(record)
            return BackupCreateResponse(
                id=record.id,
                backup_type=record.backup_type,
                status=record.status,
                backup_path=record.backup_path,
                size_bytes=record.size_bytes,
                created_at=record.created_at,
            )
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            row = self.db.get(BackupRecord, record.id)
            if row is not None:
                row.status = "failed"
                row.error_detail = str(exc)[:1900]
            if artifact.exists():
                artifact.unlink(missing_ok=True)
            if row is not None:
                self.db.commit()
            raise bad_request("VALIDATION_ERROR", f"Backup failed: {exc}") from exc
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def list_page(
        self,
        page: int,
        per_page: int,
        status: str | None,
        backup_type: str | None,
    ) -> BackupListPage:
        stmt = select(BackupRecord)
        count_stmt = select(func.count()).select_from(BackupRecord)
        if status:
            stmt = stmt.where(BackupRecord.status == status)
            count_stmt = count_stmt.where(BackupRecord.status == status)
        if backup_type:
            stmt = stmt.where(BackupRecord.backup_type == backup_type)
            count_stmt = count_stmt.where(BackupRecord.backup_type == backup_type)

        total = int(self.db.scalar(count_stmt) or 0)
        rows = self.db.scalars(
            stmt.order_by(BackupRecord.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        ).all()
        items = [
            BackupListItem(
                id=r.id,
                backup_type=r.backup_type,
                backup_path=r.backup_path,
                size_bytes=r.size_bytes,
                status=r.status,
                created_at=r.created_at,
                restored_at=r.restored_at,
            )
            for r in rows
        ]
        pages = math.ceil(total / per_page) if total else 0
        return BackupListPage(items=items, total=total, page=page, per_page=per_page, pages=pages)

    def restore(self, backup_id: uuid.UUID) -> BackupRestoreResponse:
        settings = self._settings()
        bind_url = str(self.db.get_bind().url)
        database_url = bind_url
        rec = self.db.get(BackupRecord, backup_id)
        if rec is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")
        if rec.status != "completed":
            raise bad_request("VALIDATION_ERROR", "Backup status is 'failed' and cannot be restored")

        backup_root = Path(settings.backup_root).resolve()
        artifact = Path(rec.backup_path).resolve()
        if not str(artifact).startswith(str(backup_root)) or not artifact.is_file():
            raise bad_request("VALIDATION_ERROR", "Backup artifact is missing or invalid")

        enter_maintenance()
        tmp = Path(tempfile.mkdtemp(prefix="restore_"))
        restored = datetime.now(timezone.utc)
        try:
            _extract_archive(artifact, tmp)
            sql_file = tmp / "database.sql"
            if not sql_file.exists():
                raise bad_request("VALIDATION_ERROR", "Backup archive is missing database.sql")

            uploads_src = tmp / "uploads"
            upload_dest = Path(settings.upload_root)

            if _is_postgres(database_url):
                _run_psql_file(_pg_tool_dsn(database_url), sql_file)
                _sync_upload_tree(uploads_src, upload_dest)
                rec.restored_at = restored
                self.db.commit()
            elif _is_sqlite(database_url):
                engine = self.db.get_bind()
                self.db.close()
                _restore_sqlite_engine(engine, sql_file)
                _sync_upload_tree(uploads_src, upload_dest)
                Sm = sessionmaker(bind=engine)
                with Sm() as s2:
                    row = s2.get(BackupRecord, backup_id)
                    if row is None:
                        raise bad_request("VALIDATION_ERROR", "Backup metadata missing after restore")
                    row.restored_at = restored
                    s2.commit()
            else:
                raise bad_request("VALIDATION_ERROR", "Restore not supported for this database configuration")

            return BackupRestoreResponse(
                message="System restored successfully from backup",
                backup_id=backup_id,
                restored_at=restored,
            )
        finally:
            leave_maintenance()
            shutil.rmtree(tmp, ignore_errors=True)
