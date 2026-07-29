@echo off
title POCKET
cd /d "%~dp0.."
set POCKET_ROOT=%CD%
set PYTHONPATH=%CD%\src
set POCKET_MESH_HOOK=0
set POCKET_ALWAYS_MESH=0
set POCKET_HEADLESS_AUTO=0
set POCKET_AURO_TRAIN=0
set POCKET_PORT=8787

set PY=%LOCALAPPDATA%\Programs\Python\Python311-arm64\python.exe
if not exist "%PY%" set PY=python

echo Starting POCKET host on http://127.0.0.1:8787 ...
start "POCKET-HOST" /MIN "%PY%" -u -m pocket serve --host 127.0.0.1 --port 8787

echo Waiting for health...
set /a n=0
:loop
timeout /t 1 /nobreak >nul
curl -s -m 2 http://127.0.0.1:8787/health | findstr /C:"\"ok\"" >nul
if not errorlevel 1 goto ready
set /a n+=1
if %n% LSS 40 goto loop
echo Host did not become ready. Check Python path.
pause
exit /b 1

:ready
echo Host is UP.
start "" http://127.0.0.1:8787/desk
start "" http://127.0.0.1:8787/
set EXE=%CD%\desktop-electron\node_modules\electron\dist\electron.exe
if exist "%EXE%" (
  set POCKET_URL=http://127.0.0.1:8787/desk
  start "" "%EXE%" .
)
echo.
echo POCKET is running. Keep the POCKET-HOST window minimized.
echo Desk:     http://127.0.0.1:8787/desk
echo Landing:  http://127.0.0.1:8787/
echo Login:    auto on localhost, or user pocket + password in %%USERPROFILE%%\.pocket\ACCESS.txt
echo.
pause
