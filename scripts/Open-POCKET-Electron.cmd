@echo off
title POCKET Electron
set ROOT=C:\Users\Medin\OneDrive\pocket-os
set PYTHONPATH=%ROOT%\src
set Path=C:\Users\Medin\.grok\bin;%Path%
set POCKET_PUBLIC_URL=https://pocket.medinatechlabs.net

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\Ensure-POCKET-Up.ps1" >nul 2>&1

set EXE=
if exist "%ROOT%\releases\desktop\POCKET 2.0.1-arm64.exe" set EXE=%ROOT%\releases\desktop\POCKET 2.0.1-arm64.exe
if exist "%ROOT%\releases\desktop\POCKET.2.0.1-arm64.exe" set EXE=%ROOT%\releases\desktop\POCKET.2.0.1-arm64.exe
if exist "%USERPROFILE%\Downloads\POCKET 2.0.1-arm64.exe" set EXE=%USERPROFILE%\Downloads\POCKET 2.0.1-arm64.exe

if not "%EXE%"=="" (
  start "" "%EXE%"
  exit /b 0
)

REM Fallback: desktop tray shell
start "" "%ROOT%\scripts\POCKET-Desktop-Launch.cmd"
exit /b 0
