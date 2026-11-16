@echo off
setlocal
if not exist "%~dp0update-website.ps1" (
  echo Missing required file: "%~dp0update-website.ps1"
  echo Extract the complete Fleng-Website-Latest.zip first.
  goto failed
)
if not exist "%~dp0website.patch" (
  echo Missing required file: "%~dp0website.patch"
  echo Extract the complete Fleng-Website-Latest.zip first.
  goto failed
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0update-website.ps1" %*
set "UPDATE_EXIT=%ERRORLEVEL%"
if not "%UPDATE_EXIT%"=="0" goto failed
echo.
echo GitHub update finished. Resume/deploy the existing hosting services.
pause
exit /b 0

:failed
echo.
echo Website update stopped. No successful update is confirmed. Read the message above.
pause
exit /b 1
