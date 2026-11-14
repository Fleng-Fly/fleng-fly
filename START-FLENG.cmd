@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 desktop\bootstrap.py
) else (
    python desktop\bootstrap.py
)
if errorlevel 1 pause
