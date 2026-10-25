@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\uvicorn.exe (
  echo ابتدا install.bat را اجرا کنید.
  pause
  exit /b 1
)
echo مهاجریار روی http://127.0.0.1:8000 در حال اجراست...
start "" http://127.0.0.1:8000
.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
