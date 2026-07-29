# Ensure POCKET is up. Idempotent. NEVER kills a healthy host or cloudflared.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path (Join-Path $Root "src\pocket"))) {
  $Root = "C:\Users\Medin\OneDrive\pocket-os"
}
$Src = Join-Path $Root "src"
$LogDir = Join-Path $env:USERPROFILE ".pocket"
$Log = Join-Path $LogDir "alwayson.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$py = "C:\Users\Medin\AppData\Local\Programs\Python\Python311-arm64\python.exe"
if (-not (Test-Path $py)) {
  $c = Get-Command python -ErrorAction SilentlyContinue
  if ($c) { $py = $c.Source } else { throw "Python not found" }
}

function Log([string]$m) {
  $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
  Add-Content -Path $Log -Value $line -ErrorAction SilentlyContinue
  Write-Host $line
}

function HealthOk {
  try {
    $r = Invoke-WebRequest "http://127.0.0.1:8787/" -UseBasicParsing -TimeoutSec 4
    if ($r.StatusCode -eq 200) { return $true }
  } catch {}
  try {
    $r2 = Invoke-WebRequest "http://127.0.0.1:8787/health" -UseBasicParsing -TimeoutSec 3
    if ($r2.StatusCode -eq 200) { return $true }
  } catch {}
  return $false
}

function PortListening {
  $c = Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue
  return ($null -ne $c)
}

function StartPocket {
  Log "Starting POCKET host (only because it was down)"
  $env:PYTHONPATH = $Src
  $env:POCKET_PUBLIC_URL = "https://pocket.medinatechlabs.net"
  $env:Path = "C:\Users\Medin\.grok\bin;" + $env:Path
  $envFile = Join-Path $LogDir "access.env"
  if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
      if ($_ -match '^\s*([A-Z0-9_]+)=(.*)$') {
        Set-Item -Path ("env:" + $matches[1]) -Value $matches[2].Trim()
      }
    }
  }
  $out = Join-Path $LogDir "pocket-serve.log"
  $err = Join-Path $LogDir "pocket-serve-err.log"
  Start-Process -FilePath $py -ArgumentList "-u","-m","pocket","serve","--host","0.0.0.0","--port","8787" `
    -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err | Out-Null
}

# Never kill a healthy host. Only start if down.
if (HealthOk) {
  Log "POCKET already up - leaving it alone"
  exit 0
}

if (PortListening) {
  Log "Port 8787 listening but HTTP not OK yet - waiting (not killing)"
  Start-Sleep -Seconds 5
  if (HealthOk) {
    Log "POCKET up after wait"
    exit 0
  }
  Log "Port busy but unhealthy - not auto-killing. See pocket-serve-err.log"
  exit 2
}

StartPocket
Start-Sleep -Seconds 6
if (HealthOk) {
  Log "POCKET is UP http://127.0.0.1:8787/desk"
  exit 0
}
Log "POCKET FAILED to start - see pocket-serve-err.log"
exit 1
