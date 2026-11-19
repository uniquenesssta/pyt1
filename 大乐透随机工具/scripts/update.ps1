$ErrorActionPreference = 'Stop'
try {
    $toolRoot = Split-Path -Parent $PSScriptRoot
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { throw 'Git for Windows is required.' }
    $repoRoot = & git.exe -C $toolRoot rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'This folder is not a Git checkout. Downloaded ZIP folders cannot use git pull.' }
    $origin = & git.exe -C $repoRoot remote get-url origin
    if ($LASTEXITCODE -ne 0 -or $origin -notmatch 'github\.com[:/]uniquenesssta/pyt1(?:\.git)?$') {
        throw 'The origin remote is not uniquenesssta/pyt1. No update was performed.'
    }
    $branch = & git.exe -C $repoRoot symbolic-ref --quiet --short HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Detached HEAD: switch to your working branch before updating.' }
    $upstream = & git.exe -C $repoRoot rev-parse --symbolic-full-name '@{upstream}'
    if ($LASTEXITCODE -ne 0) { throw 'The current branch has no upstream. Set its upstream before updating.' }
    $remote = & git.exe -C $repoRoot config --get "branch.$branch.remote"
    if ($LASTEXITCODE -ne 0 -or $remote -ne 'origin') {
        throw 'The current branch must track a branch on origin. No update was performed.'
    }

    # Let Git check only files touched by the update. Protect ignored files too.
    & git.exe -C $repoRoot fetch --no-recurse-submodules origin
    if ($LASTEXITCODE -ne 0) { throw 'Could not fetch from origin. See the Git output above.' }
    & git.exe -C $repoRoot merge --ff-only --no-autostash --no-overwrite-ignore -- $upstream
    if ($LASTEXITCODE -ne 0) { throw 'Git stopped the update. Review the specific reason above.' }
    Write-Host 'Update completed. Restart the tool to load the new version.'
    exit 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
