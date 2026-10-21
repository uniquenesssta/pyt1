$ErrorActionPreference = 'Stop'
try {
    $toolRoot = Split-Path -Parent $PSScriptRoot
    $pythonExe = $null
    $localPython = Join-Path $toolRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $localPython) {
        $pythonExe = $localPython
    } else {
        $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($launcher) {
            $candidate = & $launcher.Source -3 -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0) { $pythonExe = $candidate }
        }
        if (-not $pythonExe) {
            $launcher = Get-Command python.exe -ErrorAction SilentlyContinue
            if ($launcher) {
                $candidate = & $launcher.Source -c 'import sys; print(sys.executable)' 2>$null
                if ($LASTEXITCODE -eq 0) { $pythonExe = $candidate }
            }
        }
    }
    if (-not $pythonExe) { throw 'Install Python 3.10+ with Tcl/Tk, then try again.' }
    & $pythonExe -c 'import sys, tkinter; assert sys.version_info >= (3, 10), "Python 3.10+ is required"'
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ with Tcl/Tk is required.' }
    & $pythonExe -c 'import importlib.util, sys; sys.exit(0 if all(importlib.util.find_spec(n) for n in ("openpyxl", "xlrd")) else 1)'
    if ($LASTEXITCODE -ne 0) {
        if (-not (Test-Path -LiteralPath $localPython)) {
            & $pythonExe -m venv (Join-Path $toolRoot '.venv')
            if ($LASTEXITCODE -ne 0) { throw 'Could not create the local Python environment.' }
        }
        $pythonExe = $localPython
        $installLog = Join-Path $toolRoot 'dependency-install.log'
        & $pythonExe -m pip install --disable-pip-version-check -r (Join-Path $toolRoot 'requirements.txt') *> $installLog
        if ($LASTEXITCODE -ne 0) { throw "Excel dependency installation failed. Check your internet connection and $installLog" }
    }
    $pythonWindow = Join-Path (Split-Path -Parent $pythonExe) 'pythonw.exe'
    if (-not (Test-Path -LiteralPath $pythonWindow)) { throw 'pythonw.exe was not found. Repair your Python installation.' }
    $entry = Join-Path $toolRoot 'main.py'
    Start-Process -FilePath $pythonWindow -ArgumentList @('"' + $entry + '"') -WorkingDirectory $toolRoot
} catch {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Lottery tool - startup failed') | Out-Null
    exit 1
}
