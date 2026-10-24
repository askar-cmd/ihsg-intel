@echo off
REM ============================================================
REM  Pasar Intel - IHSG : jalankan server (http://localhost:8000)
REM ============================================================
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel% neq 0 (
  echo [!] Python tidak ditemukan.
  pause
  exit /b 1
)
echo [*] Menjalankan Pasar Intel di http://localhost:8000
python main.py
pause
