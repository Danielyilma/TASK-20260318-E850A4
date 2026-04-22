import uuid
from datetime import datetime
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from app.models.revoked_token import RevokedToken
from app.core.time import utcnow


def clear_blocklist(db: Session) -> None:
    db.execute(delete(RevokedToken))
    db.commit()


def revoke_jti(db: Session, jti: str, expires_at: datetime, revoked_by: uuid.UUID | None = None) -> None:
    # Cleanup old tokens occasionally
    db.execute(delete(RevokedToken).where(RevokedToken.expires_at < utcnow()))
    
    if is_jti_revoked(db, jti):
        return
        
    rt = RevokedToken(jti=jti, expires_at=expires_at, revoked_by=revoked_by)
    db.add(rt)
    db.commit()


def is_jti_revoked(db: Session, jti: str) -> bool:
    count = db.scalar(select(func.count()).select_from(RevokedToken).where(RevokedToken.jti == jti)) or 0
    return count > 0
