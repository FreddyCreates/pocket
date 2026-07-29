@echo off
REM ============================================================
REM  POCKET Desktop — double-click launcher
REM  NEVER use PowerShell "npm" (opens npm.ps1 in Notepad)
REM ============================================================
setlocal
cd /d "%~dp0.."
set POCKET_ROOT=%CD%
set POCKET_URL=http://127.0.0.1:8787/
set PYTHONPATH=%CD%\src
if exist "%USERPROFILE%\OneDrive\nexus" set PYTHONPATH=%USERPROFILE%\OneDrive\nexus;%PYTHONPATH%

REM Host via python.exe only
curl -s -o nul -m 1 http://127.0.0.1:8787/ 2>nul
if errorlevel 1 (
  if exist "%LOCALAPPDATA%\Programs\Python\Python311-arm64\python.exe" (
    start "POCKET-HOST" /MIN "%LOCALAPPDATA%\Programs\Python\Python311-arm64\python.exe" -u -m pocket serve --host 127.0.0.1 --port 8787
  ) else (
    start "POCKET-HOST" /MIN python -u -m pocket serve --host 127.0.0.1 --port 8787
  )
  timeout /t 3 /nobreak >nul
)

cd /d "%~dp0..\desktop-electron"
if not exist "node_modules\electron\package.json" (
  echo Installing Electron once via npm.cmd ...
  call "%ProgramFiles%\nodejs\npm.cmd" install --no-fund --no-audit
)

REM node run-electron.js → electron.exe  (NO npm.ps1)
node "%~dp0..\desktop-electron\run-electron.js"
endlocal
