param([switch]$SkipInstall)
$ErrorActionPreference = "Stop"
$Desktop = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Root = (Resolve-Path (Join-Path $Desktop "..")).Path
$Python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $Python) { $Python = (Get-Command python -ErrorAction Stop).Source }
if (-not $SkipInstall) {
  & $Python -m pip install --upgrade pyinstaller
  if ($LASTEXITCODE -ne 0) { throw "PyInstaller installation failed" }
}
$Out = Join-Path $Desktop "dist-host"
$Work = Join-Path $Desktop ".pyinstaller"
Remove-Item $Out,$Work -Recurse -Force -ErrorAction SilentlyContinue
& $Python -m PyInstaller --noconfirm --clean --onefile --console --name pocket-host --paths (Join-Path $Root "src") --collect-all pocket --distpath $Out --workpath $Work --specpath $Work (Join-Path $Desktop "host\entry.py")
if ($LASTEXITCODE -ne 0) { throw "POCKET host sidecar build failed" }
$Exe = Join-Path $Out "pocket-host.exe"
if (-not (Test-Path $Exe)) { throw "Missing packaged host: $Exe" }
Write-Host "POCKET_HOST_READY $Exe" -ForegroundColor Green
