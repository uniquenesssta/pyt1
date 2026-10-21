@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\update.ps1"
if errorlevel 1 (
  echo.
  echo Update failed. The error above has been retained.
  pause
  exit /b 1
)
exit /b 0
