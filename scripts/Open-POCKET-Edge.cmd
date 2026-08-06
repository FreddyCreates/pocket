@echo off
set "ROOT=%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\Ensure-POCKET-Up.ps1"
if errorlevel 1 exit /b %errorlevel%
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if exist "%EDGE%" (start "" "%EDGE%" --app=http://127.0.0.1:8787/desk --new-window) else (start "" http://127.0.0.1:8787/desk)
