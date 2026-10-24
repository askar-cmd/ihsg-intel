@echo off
REM ============================================================
REM  Pasar Intel - IHSG : install dependensi
REM ============================================================
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel% neq 0 (
  echo [!] Python tidak ditemukan. Install dulu dari https://www.python.org/downloads/
  echo     dan centang "Add Python to PATH", lalu jalankan ulang.
  pause
  exit /b 1
)
echo [*] Menginstall dependensi...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo [OK] Selesai. Jalankan dengan: python main.py
pause
