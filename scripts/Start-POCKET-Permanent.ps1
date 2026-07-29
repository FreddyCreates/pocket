# Keep POCKET Multi-Agent Console up across logon + auto-restart
# Run once as Administrator for Scheduled Task, or anytime for keep-alive loop.

$ErrorActionPreference = "Continue"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Src = Join-Path $Root "src"
$TaskName = "ITSNOTAI-POCKET-MultiAgent"

function Ensure-Firewall {
  try {
    if (-not (Get-NetFirewallRule -DisplayName "ITSNOTAI-POCKET-8787" -ErrorAction SilentlyContinue)) {
      New-NetFirewallRule -DisplayName "ITSNOTAI-POCKET-8787" -Direction Inbound -Protocol TCP -LocalPort 8787 -Action Allow -Profile Private | Out-Null
    }
  } catch {}
}

function Register-StartupTask {
  $ps = Join-Path $PSScriptRoot "Start-POCKET-Alive.ps1"
  $arg = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -File `"$ps`""
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg -WorkingDirectory $Root
  $trigger = New-ScheduledTaskTrigger -AtLogOn
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
  try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "POCKET multi-agent console always on" -Force | Out-Null
    Write-Host "Scheduled task registered: $TaskName (at logon)"
  } catch {
    Write-Host "Could not register scheduled task (try Run as Admin): $_"
    Write-Host "Falling back to keep-alive loop in this window."
  }
}

Ensure-Firewall
Register-StartupTask

# Also start now
$env:PYTHONPATH = $Src
# free port
Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep 1

Write-Host "Starting POCKET keep-alive..."
& (Join-Path $PSScriptRoot "Start-POCKET-Alive.ps1")
