@echo off
REM OWNER / OPERATOR — local host, no user onboarding (your version)
title POCKET Owner
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "PYTHONPATH=%ROOT%\src"
set "POCKET_ROOT=%ROOT%"
set "POCKET_CLIENT_ROLE=operator"
if not defined POCKET_PUBLIC_URL set "POCKET_PUBLIC_URL=https://pocket.medinatechlabs.net"

REM ensure host if down only — never thrash healthy host
if exist "%ROOT%\scripts\Ensure-POCKET-Up.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\Ensure-POCKET-Up.ps1" >nul 2>&1
)

cd /d "%ROOT%\desktop-electron"
if exist "node_modules\electron\dist\electron.exe" (
  start "POCKET Owner" "node_modules\electron\dist\electron.exe" .
  exit /b 0
)
REM fallback: Edge app local
if exist "%ROOT%\scripts\Open-POCKET-Edge.cmd" (
  start "" "%ROOT%\scripts\Open-POCKET-Edge.cmd"
  exit /b 0
)
echo Owner Electron not found. Run: cd desktop-electron ^&^& npm install
pause
exit /b 1
