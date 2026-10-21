$ErrorActionPreference = 'Stop'
try {
    $toolRoot = Split-Path -Parent $PSScriptRoot
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { throw 'Git for Windows is required.' }
    $repoRoot = & git -C $toolRoot rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'This folder is not a Git checkout. Downloaded ZIP folders cannot use git pull.' }
    $origin = & git -C $repoRoot remote get-url origin
    if ($LASTEXITCODE -ne 0 -or $origin -notmatch 'github\.com[:/]uniquenesssta/pyt1(?:\.git)?$') {
        throw 'The origin remote is not uniquenesssta/pyt1. No update was performed.'
    }
    $dirty = & git -C $repoRoot status --porcelain --untracked-files=normal
    if ($LASTEXITCODE -ne 0) { throw 'Unable to read Git status.' }
    if ($dirty) { throw 'There are local changes. Commit or move them before updating. Nothing was overwritten.' }
    & git -C $repoRoot symbolic-ref --quiet --short HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Detached HEAD: switch to your working branch before updating.' }
    & git -C $repoRoot rev-parse --abbrev-ref --symbolic-full-name '@{u}'
    if ($LASTEXITCODE -ne 0) { throw 'The current branch has no upstream. Set its upstream before updating.' }
    & git -C $repoRoot pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw 'git pull --ff-only failed. See the Git output above.' }
    Write-Host 'Update completed. Restart the tool to load the new version.'
    exit 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
