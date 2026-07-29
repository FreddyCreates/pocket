# Run the named Cloudflare tunnel for POCKET (stable, not trycloudflare quick)
# Requires Setup-Cloudflare-Named-Tunnel.ps1 completed once.

$ErrorActionPreference = "Continue"
$cf = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
if (-not (Test-Path $cf)) {
  $c = Get-Command cloudflared -EA SilentlyContinue
  if ($c) { $cf = $c.Source } else { Write-Host "cloudflared missing"; exit 1 }
}
. (Join-Path $PSScriptRoot "Use-POCKET-Auth.ps1")

$config = Join-Path $env:USERPROFILE ".cloudflared\config.yml"
if (-not (Test-Path $config)) {
  Write-Host "No named tunnel config at $config"
  Write-Host "Run first:"
  Write-Host "  powershell -File C:\Users\Medin\OneDrive\pocket-os\scripts\Setup-Cloudflare-Named-Tunnel.ps1 -Hostname pocket.YOURDOMAIN.com"
  exit 1
}

# Ensure POCKET is up
function PocketUp {
  try { $null = Invoke-WebRequest "http://127.0.0.1:8787/health" -Headers $PocketAuthHeaders -UseBasicParsing -TimeoutSec 3; return $true } catch { return $false }
}
if (-not (PocketUp)) {
  Write-Host "Starting POCKET..."
  $alive = "C:\Users\Medin\OneDrive\pocket-os\scripts\Start-POCKET-Alive.ps1"
  Start-Process -WindowStyle Minimized -FilePath powershell -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File",$alive
  for ($i=0; $i -lt 25; $i++) { Start-Sleep 1; if (PocketUp) { break } }
}
if (-not (PocketUp)) {
  Write-Host "POCKET still down on :8787 — start it, then re-run this script."
  exit 1
}

# Load public URL into env for pocket restarts
$envFile = Join-Path $env:USERPROFILE ".pocket\cloudflare-named.env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match "^\s*([A-Z0-9_]+)=(.*)$") {
      Set-Item -Path "env:$($matches[1])" -Value $matches[2].Trim()
    }
  }
  Write-Host "PUBLIC: $env:POCKET_PUBLIC_URL"
}

# Kill flaky quick tunnels / prior cloudflared
Get-Process cloudflared -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
Start-Sleep 1

Write-Host "Starting named tunnel with $config"
Write-Host "Keep this window open (or install as service via Setup ... -InstallService)."
Write-Host "Phone: $env:POCKET_PUBLIC_URL"
Write-Host "Auth:  $PocketAuthFile"
Write-Host ""

& $cf tunnel --config $config run
