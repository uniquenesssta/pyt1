$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $python = Join-Path (Get-Location) ".venv\Scripts\python.exe"
    if (-not (Test-Path $python)) { $python = (& py -3 -c "import sys; print(sys.executable)") }
    & $python -m compileall -q main.py lottery tests
    if ($LASTEXITCODE -ne 0) { throw 'Python compilation failed.' }
    & $python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Automated tests failed.' }
    Write-Host 'Compilation and tests finished. Review any SKIPPED tests above.'
    Write-Host 'Manual Windows checks: startup without console, copy/paste, resize at 100%/150% DPI, and update success/failure.'
} finally {
    Pop-Location
}
