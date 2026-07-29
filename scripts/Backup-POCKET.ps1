# Backup POCKET production state (users, keys, sessions, ledger) — no secrets to git
$ErrorActionPreference = "Stop"
$src = Join-Path $env:USERPROFILE ".pocket"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$destRoot = Join-Path $env:USERPROFILE "Documents\POCKET-backups"
$dest = Join-Path $destRoot "pocket-$stamp"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$files = @(
  "users.json",
  "api_keys.json",
  "tokenomics_ledger.json",
  "usage.json",
  "access.env",
  "ACCESS.txt",
  "INVITE.txt",
  "safety.log"
)
foreach ($f in $files) {
  $p = Join-Path $src $f
  if (Test-Path $p) { Copy-Item $p $dest -Force }
}
# dirs (shallow)
foreach ($d in @("sessions", "jobs")) {
  $p = Join-Path $src $d
  if (Test-Path $p) {
    Copy-Item $p (Join-Path $dest $d) -Recurse -Force
  }
}

# zip
$zip = Join-Path $destRoot "pocket-$stamp.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $dest -DestinationPath $zip -Force
Write-Host "Backup OK: $zip"
Write-Host "Keep offline. Do not commit to git."
