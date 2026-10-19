@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Git Pull Update
pushd "%~dp0"
if errorlevel 1 (
    echo ERROR: Cannot open the tool folder.
    pause
    exit /b 1
)
where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git was not found. Install Git for Windows and add it to PATH.
    popd
    pause
    exit /b 1
)
git rev-parse --show-toplevel >nul 2>&1
if errorlevel 1 (
    echo ERROR: This folder is not inside a Git working copy.
    echo A downloaded ZIP cannot be updated with git pull.
    popd
    pause
    exit /b 1
)
rem Parse the complete block before pulling, in case this script updates itself.
(
    echo Pulling updates...
    git -c rebase.autoStash=false -c merge.autoStash=false pull --ff-only --no-rebase
    if errorlevel 1 (
        echo.
        echo UPDATE FAILED. See the Git error above.
        echo Local changes have not been automatically discarded.
        popd
        pause
        exit /b 1
    )
    popd
    exit /b 0
)
