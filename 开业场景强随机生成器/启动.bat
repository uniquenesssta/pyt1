@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto python_fallback
py -3 app.py
goto finish
:python_fallback
python app.py
:finish
if not errorlevel 1 exit /b 0
echo.
echo Start failed. Install Python 3.10+ with Tcl/Tk, then retry.
pause
exit /b 1
