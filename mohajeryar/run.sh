#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/uvicorn ]; then
  echo "ابتدا ./install.sh را اجرا کنید." >&2
  exit 1
fi

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
echo "مهاجریار روی http://127.0.0.1:${PORT} در حال اجراست… (Ctrl+C برای توقف)"
exec ./.venv/bin/uvicorn app.main:app --host "$HOST" --port "$PORT"
