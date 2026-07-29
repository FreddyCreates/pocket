# Install POCKET always-on into Windows Startup (no admin)
$ErrorActionPreference = "Continue"
$Root = "C:\Users\Medin\OneDrive\pocket-os"
$Always = Join-Path $Root "scripts\Start-POCKET-AlwaysOn.ps1"
$Startup = [Environment]::GetFolderPath("Startup")
$cmdPath = Join-Path $Startup "POCKET-AlwaysOn.cmd"

$old = Join-Path $Startup "POCKET-MultiAgent.cmd"
if (Test-Path $old) { Remove-Item $old -Force -ErrorAction SilentlyContinue }

$cmd = "@echo off`r`n"
$cmd += "title POCKET Always-On`r`n"
$cmd += "cd /d `"$Root`"`r`n"
$cmd += "set PYTHONPATH=$Root\src`r`n"
$cmd += "set Path=C:\Users\Medin\.grok\bin;%Path%`r`n"
$cmd += "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -File `"$Always`"`r`n"
Set-Content -Path $cmdPath -Value $cmd -Encoding ASCII

Write-Host "Installed: $cmdPath"
Write-Host "Starting Always-On now..."

Start-Process -WindowStyle Minimized -FilePath "powershell" -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File",$Always

Start-Sleep 6
try {
  $h = Invoke-RestMethod http://127.0.0.1:8787/health -Headers $([scriptblock]::Create(". (Join-Path '$Root' 'scripts\\Use-POCKET-Auth.ps1'); `$PocketAuthHeaders")).Invoke() -TimeoutSec 5
  Write-Host ("POCKET UP version=" + $h.version)
} catch {
  Write-Host "Waiting for heart..."
  Start-Sleep 6
  try {
    $h2 = Invoke-RestMethod http://127.0.0.1:8787/health -Headers $([scriptblock]::Create(". (Join-Path '$Root' 'scripts\\Use-POCKET-Auth.ps1'); `$PocketAuthHeaders")).Invoke() -TimeoutSec 5
    Write-Host ("POCKET UP version=" + $h2.version)
  } catch {
    Write-Host "Check log: $env:USERPROFILE\.pocket\alwayson.log"
  }
}

Write-Host "Always-on: Startup + watchdog restarts if port 8787 dies"
Write-Host "Cloudflared service should stay Automatic for far-away tunnel"
Write-Host "Desktop: http://127.0.0.1:8787/"
