@echo off
REM ONE double-click: runtime-worker (873ms heart) + Electron desk
setlocal
cd /d "%~dp0.."
set POCKET_ROOT=%CD%
set PYTHONPATH=%CD%\src
set POCKET_PORT=8787
set POCKET_HOST=127.0.0.1
set POCKET_HEART_MS=873
set POCKET_AURO_TRAIN=0
set POCKET_URL=http://127.0.0.1:8787/desk

set PY=%LOCALAPPDATA%\Programs\Python\Python311-arm64\python.exe
if not exist "%PY%" set PY=python

REM Start runtime worker (keeps serve alive + heartbeat file)
start "POCKET-RUNTIME" /MIN "%PY%" -u -m pocket runtime-worker

REM Wait for health
set /a n=0
:wait
timeout /t 1 /nobreak >nul
curl -s -o nul -m 1 http://127.0.0.1:8787/health
if not errorlevel 1 goto open
set /a n+=1
if %n% LSS 45 goto wait

:open
set EXE=%CD%\desktop-electron\node_modules\electron\dist\electron.exe
if exist "%EXE%" (
  start "" "%EXE%" .
) else (
  start "" http://127.0.0.1:8787/desk
)
start "" http://127.0.0.1:8787/
endlocal
