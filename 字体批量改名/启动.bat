@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo Please run install.bat first.
    pause
    exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0launch.pyw"
if errorlevel 1 (
    echo Failed to start the application.
    pause
    exit /b 1
)
exit /b 0
