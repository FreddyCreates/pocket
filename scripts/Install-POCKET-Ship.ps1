# POCKET Ship Install (operator machine + dual test shortcuts)
# Always-on host on login (no admin)
# Desktop: POCKET Edge, POCKET Owner, POCKET User Test
# Does NOT kill Cloudflare or thrash servers
# Run: powershell -ExecutionPolicy Bypass -File scripts\Install-POCKET-Ship.ps1

$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path "$Root\src\pocket")) {
  $Root = "C:\Users\Medin\OneDrive\pocket-os"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " POCKET Ship Install"
Write-Host " Root: $Root"
Write-Host "========================================" -ForegroundColor Cyan

$Always = Join-Path $Root "scripts\Install-AlwaysOn.ps1"
if (Test-Path $Always) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $Always
} else {
  Write-Host "Missing Install-AlwaysOn.ps1" -ForegroundColor Yellow
}

$Ensure = Join-Path $Root "scripts\Ensure-POCKET-Up.ps1"
if (Test-Path $Ensure) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $Ensure
}

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
$deskCmd = Join-Path $Root "scripts\POCKET-Desktop-Launch.cmd"
$ownerCmd = Join-Path $Root "scripts\Open-POCKET-Owner.cmd"
$userCmd = Join-Path $Root "scripts\Open-POCKET-User.cmd"

New-Lnk (Join-Path $Desktop "POCKET.lnk") $edgeCmd -Desc "POCKET Edge owner local desk"
New-Lnk (Join-Path $Desktop "POCKET Owner.lnk") $ownerCmd -Desc "Owner Electron local host no onboarding"
New-Lnk (Join-Path $Desktop "POCKET User Test.lnk") $userCmd -Desc "User Electron pick cloud local custom first"

New-Lnk (Join-Path $StartMenu "POCKET.lnk") $edgeCmd -Desc "POCKET Edge App"
New-Lnk (Join-Path $StartMenu "POCKET Owner.lnk") $ownerCmd -Desc "Owner mode no onboarding"
New-Lnk (Join-Path $StartMenu "POCKET User.lnk") $userCmd -Desc "User mode first-run onboarding"
New-Lnk (Join-Path $StartMenu "POCKET Electron.lnk") $elecCmd -Desc "POCKET Electron portable"
New-Lnk (Join-Path $StartMenu "POCKET Desktop Tray.lnk") $deskCmd -Desc "POCKET tray and host"

$public = "https://pocket.medinatechlabs.net/desk"
New-Lnk (Join-Path $StartMenu "POCKET Cloud (phone).lnk") "cmd.exe" "/c start $public" -Desc "Open public Cloudflare desk"

Write-Host ""
Write-Host "DONE. Test both:" -ForegroundColor Green
Write-Host "  Desktop -> POCKET Owner     = YOUR version local no wizard"
Write-Host "  Desktop -> POCKET User Test = USER version source picker"
Write-Host "  Desktop -> POCKET           = Edge app local desk"
Write-Host ""
Write-Host "  Local:  http://127.0.0.1:8787/desk"
Write-Host "  Cloud:  https://pocket.medinatechlabs.net/desk"
Write-Host ""
Write-Host "Profiles isolated:"
Write-Host "  %APPDATA%\POCKET-Owner\pocket-client.json"
Write-Host "  %APPDATA%\POCKET-User\pocket-client.json"
Write-Host ""
Write-Host "Multi-user: mint pk_seat_ key as admin; members use Create my seat."
Write-Host ""