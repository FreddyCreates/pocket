@echo off
title POCKET Edge App
set ROOT=C:\Users\Medin\OneDrive\pocket-os
set PYTHONPATH=%ROOT%\src
set Path=C:\Users\Medin\.grok\bin;%Path%
set POCKET_PUBLIC_URL=https://pocket.medinatechlabs.net

REM Super-easy: start host if needed, then open Edge as an app (like any installed app)
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\Ensure-POCKET-Up.ps1" >nul 2>&1

set EDGE=
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe
if "%EDGE%"=="" (
  start "" "http://127.0.0.1:8787/desk"
  exit /b 0
)

REM App window — desk is the product surface
start "" "%EDGE%" --app=http://127.0.0.1:8787/desk --new-window
exit /b 0
