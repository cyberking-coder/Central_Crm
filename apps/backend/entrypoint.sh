#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
until python -c "import socket, os, sys; s=socket.socket(); s.settimeout(2); s.connect((os.environ['POSTGRES_HOST'], int(os.environ['POSTGRES_PORT']))); s.close()" 2>/dev/null; do
  sleep 1
done
echo "[entrypoint] Postgres reachable."

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Starting Django dev server..."
exec python manage.py runserver 0.0.0.0:8000
