# POCKET Ship Install (operator machine + easy open for you)
# - Always-on host on login (no admin)
# - Desktop + Start Menu: "POCKET" (Edge app), "POCKET Electron", "POCKET Host"
# - Does NOT kill Cloudflare or thrash servers
# Run:  powershell -ExecutionPolicy Bypass -File scripts\Install-POCKET-Ship.ps1

$ErrorActionPreference = "Continue"
$Root = "C:\Users\Medin\OneDrive\pocket-os"
if (-not (Test-Path "$Root\src\pocket")) {
  $Root = Split-Path $PSScriptRoot -Parent
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " POCKET Ship Install"
Write-Host " Root: $Root"
Write-Host "========================================" -ForegroundColor Cyan

# 1) Always-on (Startup folder — no admin)
$Always = Join-Path $Root "scripts\Install-AlwaysOn.ps1"
if (Test-Path $Always) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $Always
} else {
  Write-Host "Missing Install-AlwaysOn.ps1" -ForegroundColor Yellow
}

# 2) Ensure host is up NOW (only starts if down)
$Ensure = Join-Path $Root "scripts\Ensure-POCKET-Up.ps1"
if (Test-Path $Ensure) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $Ensure
}

# 3) Shortcuts
$Wsh = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\POCKET"
New-Item -ItemType Directory -Force -Path $StartMenu | Out-Null

function New-Lnk([string]$Path, [string]$Target, [string]$Args = "", [string]$WorkDir = $Root, [string]$Desc = "POCKET") {
  $sc = $Wsh.CreateShortcut($Path)
  $sc.TargetPath = $Target
  if ($Args) { $sc.Arguments = $Args }
  $sc.WorkingDirectory = $WorkDir
  $sc.Description = $Desc
  $edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
  if (Test-Path $edge) { $sc.IconLocation = "$edge,0" }
  $sc.Save()
  Write-Host "  + $Path"
}

$edgeCmd = Join-Path $Root "scripts\Open-POCKET-Edge.cmd"
$elecCmd = Join-Path $Root "scripts\Open-POCKET-Electron.cmd"
$hostCmd = Join-Path $env:USERPROFILE ".pocket\run-pocket.cmd"
$deskCmd = Join-Path $Root "scripts\POCKET-Desktop-Launch.cmd"

New-Lnk (Join-Path $Desktop "POCKET.lnk") $edgeCmd -Desc "POCKET Edge App (auto-starts host)"
New-Lnk (Join-Path $StartMenu "POCKET.lnk") $edgeCmd -Desc "POCKET Edge App"
New-Lnk (Join-Path $StartMenu "POCKET Electron.lnk") $elecCmd -Desc "POCKET Electron portable"
New-Lnk (Join-Path $StartMenu "POCKET Desktop Tray.lnk") $deskCmd -Desc "POCKET tray + host"
New-Lnk (Join-Path $Desktop "POCKET Electron.lnk") $elecCmd -Desc "POCKET Electron"

# Public Cloudflare (for phone / users) — open browser only, never restarts tunnel
$public = "https://pocket.medinatechlabs.net/desk"
New-Lnk (Join-Path $StartMenu "POCKET Cloud (phone).lnk") "cmd.exe" "/c start $public" -Desc "Open public Cloudflare desk"

Write-Host ""
Write-Host "DONE. Open like any app:" -ForegroundColor Green
Write-Host "  Desktop -> POCKET          (Edge app + auto host)"
Write-Host "  Desktop -> POCKET Electron"
Write-Host "  Start Menu -> POCKET"
Write-Host "  Local:  http://127.0.0.1:8787/desk"
Write-Host "  Cloud:  https://pocket.medinatechlabs.net/desk"
Write-Host ""
Write-Host "Multi-user: invite code in  $env:USERPROFILE\.pocket\INVITE.txt"
Write-Host "Users register on the login panel with that invite."
Write-Host ""
