@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found at .venv\Scripts\python.exe
    echo Run setup first:
    echo   py -3.12 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting NANPA2...
echo Open: http://127.0.0.1:5000
echo Press Ctrl+C to stop the server.
echo.

".venv\Scripts\python.exe" run.py

echo.
echo Server stopped.
pause
