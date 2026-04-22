#!/bin/sh
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
for i in $(seq 1 60); do
  if nc -z "$DB_HOST" "$DB_PORT" >/dev/null 2>&1; then
    echo "Database is reachable."
    break
  fi
  sleep 1
  if [ "$i" -eq 60 ]; then
    echo "Timed out waiting for database."
    exit 1
  fi
done

alembic upgrade head

python -m app.scripts.seed_admin

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
