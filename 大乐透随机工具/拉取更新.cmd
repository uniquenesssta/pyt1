@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\update.ps1"
set "updateStatus=%ERRORLEVEL%"
if not "%updateStatus%"=="0" (
  echo.
  echo Update stopped. See the message above for the reason.
  pause
)
exit /b %updateStatus%
