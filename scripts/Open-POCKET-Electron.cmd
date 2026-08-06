@echo off
set "ROOT=%~dp0.."
set "EXE=%LOCALAPPDATA%\Programs\POCKET\POCKET.exe"
if exist "%EXE%" (start "" "%EXE%" %* & exit /b 0)
cd /d "%ROOT%\desktop-electron"
if exist "node_modules\electron\dist\electron.exe" (start "" "node_modules\electron\dist\electron.exe" . %* & exit /b 0)
echo POCKET Desktop is not installed. Build it or download the installer from your POCKET Cloud account.
pause
