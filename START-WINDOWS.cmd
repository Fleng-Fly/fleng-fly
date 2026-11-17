@echo off
setlocal
pushd "%~dp0" >nul
if errorlevel 1 exit /b 1

where node >nul 2>nul
if errorlevel 1 goto missing_node
node -e "if (Number(process.versions.node.split('.')[0]) < 20) process.exit(1)"
if errorlevel 1 goto missing_node
if not exist "%~dp0scripts\setup.mjs" goto incomplete
if not exist "%~dp0scripts\dev.mjs" goto incomplete
if not exist "%~dp0backend\pyproject.toml" goto incomplete
if not exist "%~dp0frontend\index.html" goto incomplete

node "%~dp0scripts\setup.mjs"
if errorlevel 1 goto setup_failed

echo.
if not defined PORT set "PORT=3001"
echo When the server is ready, open http://localhost:%PORT% in your browser.
echo Keep this window open while using Fleng. Press Ctrl+C to stop.
node "%~dp0scripts\dev.mjs"
set "FLENG_EXIT=%ERRORLEVEL%"
if not "%FLENG_EXIT%"=="0" echo Fleng stopped with an error. Read the output above.
pause
popd
exit /b %FLENG_EXIT%

:missing_node
echo Node.js 20 or newer is required. Install it and open this launcher again.
goto failed

:incomplete
echo This project folder is incomplete: "%~dp0"
echo Extract the entire Fleng-Website folder from the latest ZIP.
echo Keep START-WINDOWS.cmd beside the backend, frontend and scripts folders.
goto failed

:setup_failed
echo Setup failed. Keep this window open to read the error above.

:failed
pause
popd
exit /b 1
