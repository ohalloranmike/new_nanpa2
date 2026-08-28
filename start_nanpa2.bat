@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Virtual environment not found at %PYTHON%
    echo Run setup first:
    echo   py -3.12 -m venv .venv
    echo   %PYTHON% -m pip install -r requirements.txt
    pause
    exit /b 1
)

set "NANPA_BIND=127.0.0.1:8002"
set "NANPA_PORT=8002"
for /f "delims=" %%I in ('"%PYTHON%" -c "from app.config import Config; c=Config(); print(f'{c.HOST}:{c.PORT}')" 2^>nul') do set "NANPA_BIND=%%I"
for /f "tokens=2 delims=:" %%P in ("%NANPA_BIND%") do set "NANPA_PORT=%%P"

echo Stopping any process listening on port %NANPA_PORT%...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%NANPA_PORT% "') do (
    if not "%%P"=="0" (
        echo   Ending PID %%P
        taskkill /PID %%P /F /T >nul 2>&1
    )
)
timeout /t 2 /nobreak >nul

echo.
echo Starting NANPA2...
echo Open: http://%NANPA_BIND%
echo Press Ctrl+C to stop the server.
echo.

"%PYTHON%" run.py
if errorlevel 1 goto :error
goto :eof

:error
echo.
echo The server exited with an error.
echo If the port is in use, try setting NANPA_PORT=8003 before launching.
pause
