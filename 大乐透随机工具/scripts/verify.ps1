$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    & py -3 -m compileall -q main.py lottery tests
    if ($LASTEXITCODE -ne 0) { throw 'Python compilation failed.' }
    & py -3 -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Automated tests failed.' }
    Write-Host 'Compilation and tests finished. Review any SKIPPED tests above.'
    Write-Host 'Manual Windows checks: startup without console, copy/paste, resize at 100%/150% DPI, and update success/failure.'
} finally {
    Pop-Location
}
