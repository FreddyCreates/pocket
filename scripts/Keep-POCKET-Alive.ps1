# Keep POCKET host up on :8787 (fixes "Failed to fetch")
$ErrorActionPreference = "Continue"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$env:PYTHONPATH = Join-Path $Root "src"
$py = "$env:LOCALAPPDATA\Programs\Python\Python311-arm64\python.exe"
if (-not (Test-Path $py)) { $py = "python.exe" }
$log = Join-Path $env:USERPROFILE ".pocket\pocket-serve.log"
$err = Join-Path $env:USERPROFILE ".pocket\pocket-serve-err.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

function Up {
  try {
    $r = Invoke-WebRequest "http://127.0.0.1:8787/health" -UseBasicParsing -TimeoutSec 2
    return $r.StatusCode -eq 200
  } catch { return $false }
}

Write-Host "POCKET keep-alive — Ctrl+C to stop" -ForegroundColor Cyan
while ($true) {
  if (-not (Up)) {
    Write-Host "[$(Get-Date -Format HH:mm:ss)] host down — starting..." -ForegroundColor Yellow
    Start-Process -FilePath $py -ArgumentList "-u","-m","pocket","serve","--host","0.0.0.0","--port","8787" `
      -WorkingDirectory $Root -RedirectStandardOutput $log -RedirectStandardError $err -WindowStyle Hidden
    Start-Sleep 3
    if (Up) { Write-Host "  up" -ForegroundColor Green } else { Write-Host "  still down — see $err" -ForegroundColor Red }
  }
  Start-Sleep 5
}
