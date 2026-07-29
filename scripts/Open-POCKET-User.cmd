@echo off
REM USER CLIENT — first run: pick cloud / local / custom desk (user-facing only)
title POCKET User
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "POCKET_ROOT=%ROOT%"
set "POCKET_CLIENT_ROLE=user"
REM Do not inherit operator public-url force; onboarding sets desk
set "POCKET_PUBLIC_URL=https://pocket.medinatechlabs.net"

cd /d "%ROOT%\desktop-electron"
if exist "node_modules\electron\dist\electron.exe" (
  start "POCKET User" "node_modules\electron\dist\electron.exe" .
  exit /b 0
)
if exist "%ROOT%\releases\desktop\POCKET 2.0.1-arm64.exe" (
  echo Note: packaged 2.0.1 may lack full user onboarding — prefer npm electron above.
  start "" "%ROOT%\releases\desktop\POCKET 2.0.1-arm64.exe"
  exit /b 0
)
echo Install Electron deps: cd desktop-electron ^&^& npm install
pause
exit /b 1
