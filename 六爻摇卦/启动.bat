@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 goto fail
set "TOOL_PYTHON="
set "TOOL_PYTHONW="
where py >nul 2>&1
if errorlevel 1 goto python_fallback
for /f "delims=" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "TOOL_PYTHON=%%I"
if defined TOOL_PYTHON goto launch
:python_fallback
where python >nul 2>&1
if errorlevel 1 goto fail
for /f "delims=" %%I in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "TOOL_PYTHON=%%I"
if not defined TOOL_PYTHON goto fail
:launch
for %%I in ("%TOOL_PYTHON%") do set "TOOL_PYTHONW=%%~dpIpythonw.exe"
if not exist "%TOOL_PYTHONW%" goto fail
start "" "%TOOL_PYTHONW%" "%~dp0app.pyw"
if errorlevel 1 goto fail
popd
exit /b 0
:fail
echo Start failed. Install Python 3.10+ with Tcl/Tk and pythonw.exe, then retry.
pause
exit /b 1
