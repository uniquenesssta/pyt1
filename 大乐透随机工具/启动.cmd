@echo off
setlocal
wscript.exe "%~dp0scripts\launch.vbs"
if errorlevel 1 (
  echo Unable to start Windows Script Host. Run scripts\start.ps1 with PowerShell.
  pause
  exit /b 1
)
exit /b 0
