# POCKET Always-On — keeps http://127.0.0.1:8787 up (required for Cloudflare)
$ErrorActionPreference = "Continue"
$Root = "C:\Users\Medin\OneDrive\pocket-os"
$Src = Join-Path $Root "src"
$LogDir = Join-Path $env:USERPROFILE ".pocket"
$Log = Join-Path $LogDir "alwayson.log"
$RunBat = Join-Path $LogDir "run-pocket.cmd"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$py = "C:\Users\Medin\AppData\Local\Programs\Python\Python311-arm64\python.exe"
if (-not (Test-Path $py)) {
  $c = Get-Command python -ErrorAction SilentlyContinue
  if ($c) { $py = $c.Source } else { $py = "python" }
}

function Log([string]$m) {
  $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
  Add-Content -Path $Log -Value $line -ErrorAction SilentlyContinue
  Write-Host $line
}

function HealthOk {
  try {
    $r = Invoke-RestMethod "http://127.0.0.1:8787/health" -TimeoutSec 3
    return [bool]$r.ok
  } catch { return $false }
}

function KillPort8787 {
  Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
      try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    }
  Start-Sleep -Seconds 1
}

function Read-AccessEnv {
  $user = "pocket"
  $pass = ""
  $f = Join-Path $LogDir "access.env"
  if (-not (Test-Path $f)) { $f = Join-Path $Root ".pocket\access.env" }
  if (Test-Path $f) {
    Get-Content $f | ForEach-Object {
      if ($_ -match "^\s*POCKET_BASIC_AUTH_USER=(.+)$") { $user = $Matches[1].Trim() }
      if ($_ -match "^\s*POCKET_BASIC_AUTH_PASSWORD=(.+)$") { $pass = $Matches[1].Trim() }
    }
  }
  if (-not $pass -and (Test-Path (Join-Path $LogDir "ACCESS.txt"))) {
    $t = Get-Content (Join-Path $LogDir "ACCESS.txt") -Raw
    if ($t -match "Password:\s*(\S+)") { $pass = $Matches[1] }
  }
  return @{ User = $user; Pass = $pass }
}

function StartPocket {
  $cred = Read-AccessEnv
  Log ("Starting POCKET py=$py user=$($cred.User)")
  $lines = @(
    "@echo off",
    "cd /d `"$Root`"",
    "set PYTHONPATH=$Src",
    "set Path=C:\Users\Medin\.grok\bin;%Path%",
    "set POCKET_PUBLIC_URL=https://pocket.medinatechlabs.net",
    "set POCKET_BASIC_AUTH_USER=$($cred.User)",
    "set POCKET_BASIC_AUTH_PASSWORD=$($cred.Pass)",
    "`"$py`" -m pocket serve --host 0.0.0.0 --port 8787 >> `"$LogDir\pocket-serve.log`" 2>&1"
  )
  Set-Content -Path $RunBat -Value ($lines -join "`r`n") -Encoding ASCII
  Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$RunBat`"" -WindowStyle Hidden | Out-Null
}

Log "Always-On watchdog started"
if (-not (HealthOk)) {
  KillPort8787
  StartPocket
  Start-Sleep -Seconds 5
}
if (HealthOk) { Log "HEART ok" } else { Log "HEART failed initial start — see pocket-serve.log" }

while ($true) {
  if (HealthOk) {
    # ok
  } else {
    Log "HEART STOPPED — restarting"
    KillPort8787
    StartPocket
    Start-Sleep -Seconds 6
    if (HealthOk) { Log "HEART RESTARTED" } else { Log "RESTART FAILED" }
  }
  Start-Sleep -Seconds 10
}
