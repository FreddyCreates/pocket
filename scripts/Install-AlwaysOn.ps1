$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Always = Join-Path $Root "scripts\Start-POCKET-AlwaysOn.ps1"
$Startup = [Environment]::GetFolderPath("Startup")
$Cmd = Join-Path $Startup "POCKET-AlwaysOn.cmd"
@("@echo off", "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Always`"") | Set-Content $Cmd -Encoding ASCII
Start-Process -WindowStyle Hidden -FilePath "powershell" -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File",$Always
Write-Host "Installed non-destructive POCKET startup watchdog: $Cmd"
