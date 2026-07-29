# Public phone URL via Cloudflare quick tunnel
# Keeps writing the URL to ~/.pocket/PUBLIC_URL.txt and pocket-os/PUBLIC_URL.txt

$ErrorActionPreference = "Continue"
$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cf) {
  $cfPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
  if (Test-Path $cfPath) {
    Set-Alias cloudflared $cfPath
  } else {
    Write-Host "cloudflared not found."
    exit 1
  }
}
. (Join-Path $PSScriptRoot "Use-POCKET-Auth.ps1")

function Pocket-Up {
  try {
    $null = Invoke-WebRequest "http://127.0.0.1:8787/health" -Headers $PocketAuthHeaders -UseBasicParsing -TimeoutSec 3
    return $true
  } catch { return $false }
}

if (-not (Pocket-Up)) {
  Write-Host "Starting POCKET first..."
  $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  $env:PYTHONPATH = Join-Path $Root "src"
  Start-Process -WindowStyle Minimized -FilePath "powershell" -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File",(Join-Path $PSScriptRoot "Start-POCKET-Alive.ps1")
  for ($i=0; $i -lt 20; $i++) {
    Start-Sleep 1
    if (Pocket-Up) { break }
  }
}

if (-not (Pocket-Up)) {
  Write-Host "POCKET still down on 8787 — start it manually then re-run this script."
  exit 1
}

$log = Join-Path $Pocket ".pocket\cloudflared.log"
$pub1 = Join-Path $Pocket ".pocket\PUBLIC_URL.txt"
$pub2 = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path "PUBLIC_URL.txt"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

Write-Host "Starting cloudflared tunnel -> http://127.0.0.1:8787"
Write-Host "Log: $log"
Write-Host "Phone: wait for trycloudflare.com URL below, then open it."
Write-Host "Auth:  $PocketAuthFile"
Write-Host ""

# Run tunnel; watch log for URL
$exe = if (Test-Path "C:\Program Files (x86)\cloudflared\cloudflared.exe") {
  "C:\Program Files (x86)\cloudflared\cloudflared.exe"
} else { "cloudflared" }

$p = Start-Process -FilePath $exe -ArgumentList @("tunnel","--url","http://127.0.0.1:8787") `
  -RedirectStandardError $log -RedirectStandardOutput $log -PassThru -NoNewWindow

$found = $null
for ($i=0; $i -lt 60; $i++) {
  Start-Sleep 1
  if (Test-Path $log) {
    $txt = Get-Content $log -Raw -ErrorAction SilentlyContinue
    if ($txt -match "https://[a-z0-9-]+\.trycloudflare\.com") {
      $found = $Matches[0]
      break
    }
  }
  if ($p.HasExited) { break }
}

if ($found) {
  $msg = @"
POCKET PUBLIC URL
$found

PC:    http://127.0.0.1:8787/
PHONE: $found   (or LAN if same Wi-Fi)
Note: quick tunnels can flap. Keep this script running.
Auth:  $PocketAuthFile
"@
  Set-Content $pub1 $msg
  Set-Content $pub2 $msg
  $env:POCKET_PUBLIC_URL = $found
  Write-Host "========================================" -ForegroundColor Green
  Write-Host " PHONE URL: $found" -ForegroundColor Green
  Write-Host " Saved to $pub1" -ForegroundColor Green
  Write-Host " Keep this window open." -ForegroundColor Green
  Write-Host "========================================" -ForegroundColor Green
} else {
  Write-Host "No URL yet — check $log"
}

# Keep process attached
Wait-Process -Id $p.Id

