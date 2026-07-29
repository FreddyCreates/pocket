# POCKET multi-agent keep-alive — leave this window open (or use Permanent script)
$ErrorActionPreference = "Continue"
if (-not $PSScriptRoot) { $PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path }
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Src = Join-Path $Root "src"
. (Join-Path $PSScriptRoot "Use-POCKET-Auth.ps1")
$env:PYTHONPATH = $Src
Set-Location -LiteralPath $Root

try {
  if (-not (Get-NetFirewallRule -DisplayName "ITSNOTAI-POCKET-8787" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName "ITSNOTAI-POCKET-8787" -Direction Inbound -Protocol TCP -LocalPort 8787 -Action Allow -Profile Private | Out-Null
  }
} catch {}

function Get-LanIp {
  try {
    return (Get-NetIPAddress -AddressFamily IPv4 |
      Where-Object { $_.IPAddress -like "192.168.*" } |
      Select-Object -First 1 -ExpandProperty IPAddress)
  } catch { return "192.168.x.x" }
}

$lan = Get-LanIp
Write-Host ""
Write-Host "============================================"
Write-Host " POCKET Multi-Agent Console (keep-alive)"
Write-Host " Desktop: http://127.0.0.1:8787/"
Write-Host " Phone:   http://${lan}:8787/"
Write-Host " Root=$Root"
Write-Host " Auth:    $PocketAuthFile"
Write-Host "============================================"
Write-Host ""

while ($true) {
  Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
  Start-Sleep -Seconds 1
  Write-Host ("[{0}] python -m pocket serve" -f (Get-Date -Format "HH:mm:ss"))
  try {
    python -m pocket serve --host 0.0.0.0 --port 8787
  } catch {
    Write-Host "error: $_"
  }
  Write-Host ("[{0}] exited — restart in 2s" -f (Get-Date -Format "HH:mm:ss"))
  Start-Sleep -Seconds 2
}
