@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto fail
".venv\Scripts\python.exe" -m pip install pyinstaller
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name FontBatchRenamer app.py
if errorlevel 1 goto fail
echo Built: dist\FontBatchRenamer.exe
pause
exit /b 0
:fail
echo Build failed. Run install.bat first and review the error above.
pause
exit /b 1
