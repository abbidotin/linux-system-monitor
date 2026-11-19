@echo off
REM Quick launcher script for Windows environments

setlocal
cd /d "%~dp0"

REM Determine mode
set MODE=%1
if "%MODE%"=="" set MODE=snapshot

echo Running System Health Monitor in mode: %MODE%
py -3 main.py %*
if errorlevel 1 (
    python main.py %*
)
endlocal
