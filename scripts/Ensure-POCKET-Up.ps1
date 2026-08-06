# Idempotent local starter. Never kills or restarts a healthy process.
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Port = 8787
function Healthy { try { return (Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 3).ok -eq $true } catch { return $false } }
if (Healthy) { Write-Host "POCKET already healthy; leaving it untouched."; exit 0 }
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
  Write-Error "Port $Port is occupied but POCKET health failed. Refusing to kill or replace that process."
  exit 2
}
$Exe = Join-Path $Root "desktop-electron\dist-host\pocket-host.exe"
if (Test-Path $Exe) {
  Start-Process -FilePath $Exe -ArgumentList "--host","127.0.0.1","--port","$Port" -WindowStyle Hidden | Out-Null
} else {
  $Python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
  if (-not $Python) { $Python = (Get-Command python -ErrorAction Stop).Source }
  $env:PYTHONPATH = Join-Path $Root "src"
  Start-Process -FilePath $Python -ArgumentList "-u","-m","pocket","serve","--host","127.0.0.1","--port","$Port" -WorkingDirectory $Root -WindowStyle Hidden | Out-Null
}
$deadline=(Get-Date).AddSeconds(45)
do { Start-Sleep -Milliseconds 500; if (Healthy) { Write-Host "POCKET is healthy at http://127.0.0.1:$Port/desk"; exit 0 } } while ((Get-Date) -lt $deadline)
Write-Error "POCKET did not become healthy."
exit 1
