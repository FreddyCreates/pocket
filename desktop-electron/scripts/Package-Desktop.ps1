param(
  [ValidateSet("x64", "arm64")]
  [string]$Arch = "x64"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root

$package = Get-Content (Join-Path $root "package.json") -Raw | ConvertFrom-Json
$version = [string]$package.version
$sharedName = "POCKET-Desktop-$version-$Arch.exe"
$sharedPath = Join-Path $root "dist/$sharedName"
$setupPath = Join-Path $root "dist/POCKET-Setup-$version-$Arch.exe"
$portablePath = Join-Path $root "dist/POCKET-Portable-$version-$Arch.exe"

New-Item -ItemType Directory -Path (Join-Path $root "dist") -Force | Out-Null
Remove-Item $setupPath, $portablePath -Force -ErrorAction SilentlyContinue

Write-Host "Building POCKET NSIS installer for $Arch"
& npx electron-builder --win nsis "--$Arch"
if ($LASTEXITCODE -ne 0) { throw "electron-builder NSIS failed with exit code $LASTEXITCODE" }
if (-not (Test-Path $sharedPath)) { throw "Expected NSIS artifact was not created: $sharedPath" }
Move-Item $sharedPath $setupPath -Force

Write-Host "Building POCKET portable application for $Arch"
& npx electron-builder --win portable "--$Arch"
if ($LASTEXITCODE -ne 0) { throw "electron-builder portable failed with exit code $LASTEXITCODE" }
if (-not (Test-Path $sharedPath)) { throw "Expected portable artifact was not created: $sharedPath" }
Move-Item $sharedPath $portablePath -Force

$edgeLauncher = @"
@echo off
setlocal
set "POCKET_EXE=%~dp0POCKET-Portable-$version-$Arch.exe"
if not exist "%POCKET_EXE%" (
  echo POCKET portable application was not found next to this launcher.
  exit /b 2
)
start "POCKET Edge" "%POCKET_EXE%" --edge
"@
$localLauncher = @"
@echo off
setlocal
set "POCKET_EXE=%~dp0POCKET-Portable-$version-$Arch.exe"
if not exist "%POCKET_EXE%" (
  echo POCKET portable application was not found next to this launcher.
  exit /b 2
)
start "POCKET Local" "%POCKET_EXE%" --local
"@
$cloudLauncher = @"
@echo off
setlocal
set "POCKET_EXE=%~dp0POCKET-Portable-$version-$Arch.exe"
if not exist "%POCKET_EXE%" (
  echo POCKET portable application was not found next to this launcher.
  exit /b 2
)
start "POCKET Cloud" "%POCKET_EXE%" --cloud
"@

Set-Content -Path (Join-Path $root "dist/POCKET-Edge-$Arch.cmd") -Value $edgeLauncher -Encoding Ascii
Set-Content -Path (Join-Path $root "dist/POCKET-Local-$Arch.cmd") -Value $localLauncher -Encoding Ascii
Set-Content -Path (Join-Path $root "dist/POCKET-Cloud-$Arch.cmd") -Value $cloudLauncher -Encoding Ascii

$artifacts = @($setupPath, $portablePath)
$manifest = @{
  schema = "pocket.desktop.artifacts.v1"
  product = "POCKET"
  version = $version
  arch = $Arch
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  artifacts = @()
}
foreach ($artifact in $artifacts) {
  $item = Get-Item $artifact
  $manifest.artifacts += @{
    name = $item.Name
    bytes = $item.Length
    sha256 = (Get-FileHash $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
  }
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $root "dist/POCKET-Desktop-$version-$Arch-SHA256.json") -Encoding UTF8

Write-Host "POCKET desktop artifacts ready:"
Get-ChildItem (Join-Path $root "dist") -File | Where-Object { $_.Name -match "POCKET-(Setup|Portable|Edge|Local|Cloud|Desktop).*($Arch)" } | ForEach-Object {
  Write-Host " - $($_.Name) ($($_.Length) bytes)"
}
