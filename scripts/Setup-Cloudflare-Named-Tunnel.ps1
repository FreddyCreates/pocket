# POCKET — real Cloudflare Named Tunnel (paid account)
# Run in an interactive PowerShell window (browser login required once).
#
# What this does:
#  1) cloudflared tunnel login  (opens browser → pick your zone)
#  2) creates tunnel "pocket-os" (or name you pass)
#  3) writes config.yml pointing hostname → http://127.0.0.1:8787
#  4) routes DNS CNAME for your hostname
#  5) optional: install as Windows service (stable when you're far)
#
# Usage:
#   powershell -File Setup-Cloudflare-Named-Tunnel.ps1 -Hostname pocket.yourdomain.com
#   powershell -File Setup-Cloudflare-Named-Tunnel.ps1 -Hostname pocket.yourdomain.com -InstallService

param(
  [Parameter(Mandatory = $false)]
  [string]$Hostname = "",

  [string]$TunnelName = "pocket-os",

  [string]$LocalService = "http://127.0.0.1:8787",

  [switch]$InstallService,

  [switch]$SkipLogin
)

$ErrorActionPreference = "Stop"
$cf = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
if (-not (Test-Path $cf)) {
  $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
  if ($cmd) { $cf = $cmd.Source } else { throw "cloudflared not found. Install from Cloudflare." }
}

$cfDir = Join-Path $env:USERPROFILE ".cloudflared"
New-Item -ItemType Directory -Force -Path $cfDir | Out-Null
$pocketDir = Join-Path $env:USERPROFILE ".pocket"
New-Item -ItemType Directory -Force -Path $pocketDir | Out-Null

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " POCKET Named Cloudflare Tunnel Setup"
Write-Host " cloudflared: $cf"
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (-not $Hostname) {
  Write-Host "Enter the public hostname you own on Cloudflare DNS."
  Write-Host "Example: pocket.yourdomain.com  (domain must be on this CF account)"
  $Hostname = Read-Host "Hostname"
  if (-not $Hostname) { throw "Hostname required" }
}

$Hostname = $Hostname.Trim().ToLower()
Write-Host "Tunnel name : $TunnelName"
Write-Host "Hostname    : $Hostname"
Write-Host "Local       : $LocalService"
Write-Host ""

# --- 1) Login (cert.pem) ---
$cert = Join-Path $cfDir "cert.pem"
if (-not $SkipLogin -or -not (Test-Path $cert)) {
  if (-not (Test-Path $cert)) {
    Write-Host "Opening browser for Cloudflare login..." -ForegroundColor Yellow
    Write-Host "Pick the domain/zone you want to use, then return here."
    & $cf tunnel login
    if (-not (Test-Path $cert)) {
      throw "Login did not produce cert.pem at $cert — re-run login."
    }
    Write-Host "Login OK: $cert" -ForegroundColor Green
  } else {
    Write-Host "Already logged in ($cert)" -ForegroundColor Green
  }
}

# --- 2) Create tunnel if missing ---
$tunnelId = $null
$listJson = & $cf tunnel list --output json 2>$null
if ($listJson) {
  try {
    $tunnels = $listJson | ConvertFrom-Json
    $existing = $tunnels | Where-Object { $_.name -eq $TunnelName } | Select-Object -First 1
    if ($existing) {
      $tunnelId = $existing.id
      Write-Host "Tunnel exists: $TunnelName id=$tunnelId" -ForegroundColor Green
    }
  } catch {}
}

if (-not $tunnelId) {
  Write-Host "Creating tunnel $TunnelName ..."
  $createOut = & $cf tunnel create $TunnelName 2>&1 | Out-String
  Write-Host $createOut
  # credentials file: ~/.cloudflared/<uuid>.json
  $cred = Get-ChildItem $cfDir -Filter "*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $cred) { throw "No credentials JSON after tunnel create in $cfDir" }
  # parse id from filename or list again
  $listJson = & $cf tunnel list --output json 2>$null
  $tunnels = $listJson | ConvertFrom-Json
  $existing = $tunnels | Where-Object { $_.name -eq $TunnelName } | Select-Object -First 1
  if (-not $existing) { throw "Tunnel create failed — not listed" }
  $tunnelId = $existing.id
  Write-Host "Created tunnel id=$tunnelId" -ForegroundColor Green
}

$credFile = Join-Path $cfDir "$tunnelId.json"
if (-not (Test-Path $credFile)) {
  # sometimes named differently
  $credFile = (Get-ChildItem $cfDir -Filter "*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
}
if (-not (Test-Path $credFile)) { throw "Missing credentials file for tunnel $tunnelId" }

# --- 3) Write config.yml ---
$configPath = Join-Path $cfDir "config.yml"
$config = @"
# POCKET named tunnel — managed by Setup-Cloudflare-Named-Tunnel.ps1
tunnel: $tunnelId
credentials-file: $credFile

ingress:
  - hostname: $Hostname
    service: $LocalService
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
  # catch-all required
  - service: http_status:404
"@
Set-Content -Path $configPath -Value $config -Encoding UTF8
Write-Host "Wrote $configPath" -ForegroundColor Green

# --- 4) DNS route ---
Write-Host "Routing DNS $Hostname -> tunnel $TunnelName ..."
try {
  & $cf tunnel route dns $TunnelName $Hostname 2>&1 | Write-Host
  Write-Host "DNS route OK (CNAME created/updated in Cloudflare DNS)" -ForegroundColor Green
} catch {
  Write-Host "DNS route warning: $_" -ForegroundColor Yellow
  Write-Host "You can add CNAME $Hostname -> $tunnelId.cfargotunnel.com manually in CF DNS."
}

# --- 5) Save POCKET public URL ---
$publicUrl = "https://$Hostname/"
$msg = @"
POCKET NAMED TUNNEL
PUBLIC: $publicUrl
DESKTOP: http://127.0.0.1:8787/
LAN: (same Wi-Fi only)

tunnel: $TunnelName
id: $tunnelId
config: $configPath
hostname: $Hostname
local: $LocalService
"@
Set-Content (Join-Path $pocketDir "PUBLIC_URL.txt") $msg
Set-Content (Join-Path $pocketDir "cloudflare-named.env") @"
POCKET_PUBLIC_URL=https://$Hostname
POCKET_CF_TUNNEL=$TunnelName
POCKET_CF_TUNNEL_ID=$tunnelId
POCKET_CF_HOSTNAME=$Hostname
"@
$repoPub = "C:\Users\Medin\OneDrive\pocket-os\PUBLIC_URL.txt"
if (Test-Path (Split-Path $repoPub)) { Set-Content $repoPub $msg }

Write-Host ""
Write-Host "PUBLIC URL: $publicUrl" -ForegroundColor Green

# --- 6) Optional Windows service ---
if ($InstallService) {
  Write-Host "Installing cloudflared Windows service..."
  try {
    # stop quick tunnels
    Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    & $cf service uninstall 2>$null | Out-Null
    & $cf service install
    Start-Service cloudflared -ErrorAction SilentlyContinue
    Write-Host "Service installed. Tunnel should start with Windows." -ForegroundColor Green
  } catch {
    Write-Host "Service install needs Administrator. Run this script elevated with -InstallService" -ForegroundColor Yellow
    Write-Host "Or run: Start-Cloudflare-Named.ps1 in a keep-alive window."
  }
} else {
  Write-Host ""
  Write-Host "Next: start the tunnel (keep running while you're far):" -ForegroundColor Cyan
  Write-Host "  powershell -File C:\Users\Medin\OneDrive\pocket-os\scripts\Start-Cloudflare-Named.ps1"
  Write-Host "Or re-run this script with -InstallService as Admin for always-on."
}

Write-Host ""
Write-Host "Also keep POCKET up:" -ForegroundColor Cyan
Write-Host "  powershell -File C:\Users\Medin\OneDrive\pocket-os\scripts\Start-POCKET-NoAdmin.ps1"
Write-Host ""
Write-Host "Done. Phone from anywhere: $publicUrl" -ForegroundColor Green
