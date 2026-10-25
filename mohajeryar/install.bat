@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10+ را نصب کنید و دوباره اجرا کنید.
  pause
  exit /b 1
)

if not exist .venv (
  echo ساخت محیط مجازی...
  python -m venv .venv
)

echo نصب وابستگی‌ها...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt

if not exist .env copy .env.example .env >nul

if not exist data mkdir data
echo.
echo نصب کامل شد. برای اجرا run.bat را بزنید.
pause
