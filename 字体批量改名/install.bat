@echo off
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Installation completed.
pause
exit /b 0
:fail
echo Installation failed. Install Python 3.10+ with Tcl/Tk and Python Launcher.
pause
exit /b 1
