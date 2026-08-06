# Install portable shortcuts without depending on a personal source path.
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\POCKET"; New-Item -ItemType Directory -Force $StartMenu | Out-Null
$Wsh = New-Object -ComObject WScript.Shell
function Shortcut($Path,$Target,$Description) { $s=$Wsh.CreateShortcut($Path);$s.TargetPath=$Target;$s.WorkingDirectory=$Root;$s.Description=$Description;$s.Save() }
Shortcut (Join-Path $Desktop "POCKET Edge.lnk") (Join-Path $Root "scripts\Open-POCKET-Edge.cmd") "POCKET local Edge app"
Shortcut (Join-Path $StartMenu "POCKET Edge.lnk") (Join-Path $Root "scripts\Open-POCKET-Edge.cmd") "POCKET local Edge app"
Shortcut (Join-Path $StartMenu "POCKET Desktop.lnk") (Join-Path $Root "scripts\Open-POCKET-Electron.cmd") "POCKET Electron desktop"
Write-Host "Shortcuts installed. The packaged Electron installer creates its own Desktop and Start-menu shortcuts."
