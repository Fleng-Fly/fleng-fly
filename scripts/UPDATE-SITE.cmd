@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0update-site.ps1" %*
if errorlevel 1 (
  echo.
  echo Website update stopped. Read the message above.
  pause
  exit /b 1
)
echo.
echo GitHub update finished. Resume/deploy the existing hosting services.
pause
