# Start POCKET Remote Agent Console (phone -> Codex/Claude on this PC)
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
# scripts/ is under pocket-os
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Src = Join-Path $Root "src"
. (Join-Path $PSScriptRoot "Use-POCKET-Auth.ps1")

Write-Host "Stopping anything on :8787 ..."
Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

$env:PYTHONPATH = $Src
Set-Location $Root

$lan = $null
try {
  $lan = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -like '192.168.*' -or $_.IPAddress -like '10.*' } |
    Select-Object -First 1 -ExpandProperty IPAddress)
} catch {}
if (-not $lan) { $lan = "192.168.x.x" }

@"
POCKET STATUS - $(Get-Date -Format o)

WORKING:
  PC:     http://127.0.0.1:8787/
  PHONE:  http://${lan}:8787/

Value: phone sends job -> Codex/Claude runs on THIS PC -> full result on phone.
Same Wi-Fi required. Keep this window open.
Auth:   $PocketAuthFile
"@ | Set-Content (Join-Path $Root "PUBLIC_URL.txt")

Write-Host ""
Write-Host "POCKET Remote Agent" -ForegroundColor Cyan
Write-Host "  PC:    http://127.0.0.1:8787/"
Write-Host "  PHONE: http://${lan}:8787/   << open on phone (same Wi-Fi)"
Write-Host "  Auth:  $PocketAuthFile"
Write-Host "  Keep this window open while using the phone."
Write-Host ""

python -m pocket serve --host 0.0.0.0 --port 8787
