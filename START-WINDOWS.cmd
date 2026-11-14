@echo off
setlocal
cd /d "%~dp0"

call npm run setup
if errorlevel 1 (
    echo.
    echo Setup failed. Keep this window open to read the error.
    pause
    exit /b 1
)

echo.
echo When the server is ready, open http://localhost:3001 in your browser.
echo Keep this window open while using Fleng. Press Ctrl+C to stop.
call npm run dev
pause
