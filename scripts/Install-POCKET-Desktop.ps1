# Install POCKET Desktop for the current user:
#   · Desktop shortcut
#   · Start Menu shortcut
#   · Startup (always-on tray + runtime on login)
#   · Uninstall helper written beside install

$ErrorActionPreference = "Stop"
$Root = "C:\Users\Medin\OneDrive\pocket-os"
if (-not (Test-Path "$Root\src\pocket")) {
  $Root = Split-Path $PSScriptRoot -Parent
}

$pyCandidates = @(
  "$env:LOCALAPPDATA\Programs\Python\Python311-arm64\python.exe",
  "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
  (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
) | Where-Object { $_ -and (Test-Path $_) }
$Python = $pyCandidates | Select-Object -First 1
if (-not $Python) { throw "Python not found" }

Write-Host "POCKET Desktop install" -ForegroundColor Cyan
Write-Host "  Root:   $Root"
Write-Host "  Python: $Python"

# deps for tray
& $Python -m pip install pystray pillow --quiet

$Wsh = New-Object -ComObject WScript.Shell

function New-PocketShortcut([string]$Path, [string]$ArgsExtra = "") {
  $sc = $Wsh.CreateShortcut($Path)
  $sc.TargetPath = $Python
  $sc.Arguments = "-m pocket desktop $ArgsExtra".Trim()
  $sc.WorkingDirectory = $Root
  $sc.WindowStyle = 7  # minimized - tray is primary
  $sc.Description = "POCKET Desktop - host co-pilot (Fusion Sense)"
  # icon: use python or edge if no custom ico
  $edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
  if (Test-Path $edge) { $sc.IconLocation = "$edge,0" }
  $sc.Save()
  Write-Host "  + $Path"
}

# Env for shortcuts: need PYTHONPATH - wrap via a small launcher cmd
$Launcher = Join-Path $Root "scripts\POCKET-Desktop-Launch.cmd"
@"
@echo off
set PYTHONPATH=$Root\src
if exist "%USERPROFILE%\OneDrive\nexus" (
  set PYTHONPATH=%USERPROFILE%\OneDrive\nexus;%PYTHONPATH%
  set NEXUS_ROOT=%USERPROFILE%\OneDrive\nexus
)
cd /d "$Root"
start "" "$Python" -m pocket desktop
"@ | Set-Content -Encoding ASCII $Launcher

function New-CmdShortcut([string]$Path, [string]$CmdPath, [int]$WindowStyle = 7) {
  $sc = $Wsh.CreateShortcut($Path)
  $sc.TargetPath = $CmdPath
  $sc.WorkingDirectory = $Root
  $sc.WindowStyle = $WindowStyle
  $sc.Description = "POCKET Desktop"
  $edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
  if (Test-Path $edge) { $sc.IconLocation = "$edge,0" }
  $sc.Save()
  Write-Host "  + $Path"
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\POCKET"
$Startup = [Environment]::GetFolderPath("Startup")
New-Item -ItemType Directory -Force -Path $StartMenu | Out-Null

New-CmdShortcut (Join-Path $Desktop "POCKET Desktop.lnk") $Launcher 1
New-CmdShortcut (Join-Path $StartMenu "POCKET Desktop.lnk") $Launcher 1
New-CmdShortcut (Join-Path $StartMenu "POCKET Desktop (tray).lnk") $Launcher 7
New-CmdShortcut (Join-Path $Startup "POCKET Desktop.lnk") $Launcher 7

# Always-on runtime companion (serve even without tray if desired)
$AlwaysOn = Join-Path $Root "scripts\Start-POCKET-AlwaysOn.ps1"
if (Test-Path $AlwaysOn) {
  $sc = $Wsh.CreateShortcut((Join-Path $StartMenu "POCKET Runtime AlwaysOn.lnk"))
  $sc.TargetPath = "powershell.exe"
  $sc.Arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$AlwaysOn`""
  $sc.WorkingDirectory = $Root
  $sc.WindowStyle = 7
  $sc.Description = "POCKET HTTP runtime always-on"
  $sc.Save()
  Write-Host "  + Start Menu: POCKET Runtime AlwaysOn"
}

# Uninstall script
$Uninstall = Join-Path $Root "scripts\Uninstall-POCKET-Desktop.ps1"
@"
# Remove POCKET Desktop shortcuts for current user
Remove-Item -Force -ErrorAction SilentlyContinue "$Desktop\POCKET Desktop.lnk"
Remove-Item -Force -ErrorAction SilentlyContinue "$Startup\POCKET Desktop.lnk"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$StartMenu"
Write-Host "POCKET Desktop shortcuts removed. Runtime files under ~/.pocket kept."
"@ | Set-Content -Encoding UTF8 $Uninstall

# Record install manifest
$manifest = @{
  installed_at = (Get-Date).ToString("o")
  root = $Root
  python = $Python
  desktop = (Join-Path $Desktop "POCKET Desktop.lnk")
  start_menu = $StartMenu
  startup = (Join-Path $Startup "POCKET Desktop.lnk")
  launcher = $Launcher
}
$manifestPath = Join-Path $env:USERPROFILE ".pocket\desktop-install.json"
New-Item -ItemType Directory -Force -Path (Split-Path $manifestPath) | Out-Null
$manifest | ConvertTo-Json | Set-Content -Encoding UTF8 $manifestPath

Write-Host ""
Write-Host "Installed." -ForegroundColor Green
Write-Host "  Desktop:   POCKET Desktop.lnk"
Write-Host "  Start:     Start Menu → POCKET"
Write-Host "  Startup:   logs in with tray + runtime"
Write-Host "  Uninstall: $Uninstall"
Write-Host ""
Write-Host "Launching POCKET Desktop now..." -ForegroundColor Cyan
Start-Process -FilePath $Launcher
