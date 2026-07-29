# POCKET for REAL PHONE use (public HTTPS via cloudflared)
# 1) Starts POCKET on :8787
# 2) Opens a Cloudflare quick tunnel -> URL works on phone even off home Wi-Fi
# You do NOT need your phone number for this (it's a web app).

$ErrorActionPreference = "Stop"
$Pocket = "C:\Users\Medin\OneDrive\pocket-os"
$Hz = "C:\Users\Medin\OneDrive\hz-offline"
$env:PYTHONPATH = "$Pocket\src;$Hz\src"
. (Join-Path $Pocket "scripts\Use-POCKET-Auth.ps1")

$cf = @(
  "C:\Program Files (x86)\cloudflared\cloudflared.exe",
  "C:\Program Files\cloudflared\cloudflared.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $cf) {
  Write-Host "cloudflared not found. Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/" -ForegroundColor Red
  Write-Host "Or use same-WiFi only: http://YOUR-LAN-IP:8787/"
  exit 1
}

# free 8787
Get-NetTCPConnection -LocalPort 8787 -State Listen -EA SilentlyContinue | ForEach-Object {
  Stop-Process -Id $_.OwningProcess -Force -EA SilentlyContinue
}
Start-Sleep 1

Write-Host "Starting POCKET on :8787 ..." -ForegroundColor Cyan
$pocketScript = @"
`$env:PYTHONPATH = '$Pocket\src;$Hz\src'
Set-Location '$Pocket'
. '$Pocket\scripts\Use-POCKET-Auth.ps1'
python -m pocket serve --host 0.0.0.0 --port 8787
"@
$ps1 = Join-Path $env:TEMP "pocket-serve.ps1"
[IO.File]::WriteAllText($ps1, $pocketScript)
Start-Process powershell -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File",$ps1

Start-Sleep 2

# Write public URL as we discover it
$urlFile = Join-Path $Pocket "PUBLIC_URL.txt"
if (Test-Path $urlFile) { Remove-Item $urlFile -Force }

Write-Host "Starting Cloudflare tunnel (phone URL will print below)..." -ForegroundColor Yellow
Write-Host "Leave this window open. Copy the https://....trycloudflare.com URL to your phone." -ForegroundColor Green
Write-Host "Auth file: $PocketAuthFile" -ForegroundColor DarkYellow
Write-Host ""

# Run cloudflared in this window so user sees the URL
& $cf tunnel --url http://127.0.0.1:8787
