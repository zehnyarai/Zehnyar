#!/usr/bin/env bash
# نصب یک‌مرحله‌ای مهاجریار
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "پایتون ۳ یافت نشد. ابتدا Python 3.10+ را نصب کنید." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  echo "→ ساخت محیط مجازی…"
  "$PYTHON" -m venv .venv
fi

echo "→ نصب وابستگی‌ها…"
./.venv/bin/pip install --upgrade pip >/dev/null
./.venv/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "→ فایل .env ساخته شد (برای فعال‌سازی مشاور هوشمند GROQ_API_KEY را پر کنید)."
fi

chmod +x run.sh
mkdir -p data
echo
echo "✅ نصب کامل شد. برای اجرا:  ./run.sh"
echo "   سپس در مرورگر:        http://127.0.0.1:8000"
