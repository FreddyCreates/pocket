# Non-destructive watchdog: start only when absent; never terminate listeners.
$ErrorActionPreference = "Continue"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Ensure = Join-Path $Root "scripts\Ensure-POCKET-Up.ps1"
$LogDir = Join-Path $env:USERPROFILE ".pocket"; New-Item -ItemType Directory -Force $LogDir | Out-Null
$Log = Join-Path $LogDir "alwayson.log"
function Write-Log($Message) { $line="[{0}] {1}" -f (Get-Date -Format "s"),$Message; Add-Content $Log $line; Write-Host $line }
Write-Log "Non-destructive watchdog started"
while ($true) {
  try { & powershell -NoProfile -ExecutionPolicy Bypass -File $Ensure | ForEach-Object { Write-Log $_ } }
  catch { Write-Log "Ensure failed: $_" }
  Start-Sleep -Seconds 20
}
