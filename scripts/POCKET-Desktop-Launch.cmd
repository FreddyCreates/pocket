@echo off
set PYTHONPATH=C:\Users\Medin\OneDrive\pocket-os\src
if exist "%USERPROFILE%\OneDrive\nexus" (
  set PYTHONPATH=%USERPROFILE%\OneDrive\nexus;%PYTHONPATH%
  set NEXUS_ROOT=%USERPROFILE%\OneDrive\nexus
)
cd /d "C:\Users\Medin\OneDrive\pocket-os"
start "" "C:\Users\Medin\AppData\Local\Programs\Python\Python311-arm64\python.exe" -m pocket desktop
