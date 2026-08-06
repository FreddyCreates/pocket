param(
  [ValidateSet("auto", "x64", "arm64", "both")][string]$Arch = "auto",
  [switch]$SkipInstall,
  [switch]$SkipHostBuild
)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Desktop = Join-Path $Root "desktop-electron"
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npm) { $npm = (Get-Command npm -ErrorAction Stop).Source }
if ($Arch -eq "auto") {
  $machine = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
  $Arch = if ($machine -match "arm64") { "arm64" } else { "x64" }
}
if (-not $SkipHostBuild) {
  $hostArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Desktop "scripts\Build-Host.ps1"))
  if ($SkipInstall) { $hostArgs += "-SkipInstall" }
  & powershell @hostArgs
  if ($LASTEXITCODE -ne 0) { throw "POCKET host sidecar build failed" }
}
if (-not (Test-Path (Join-Path $Desktop "dist-host\pocket-host.exe"))) { throw "Packaged host is missing" }
Push-Location $Desktop
try {
  if (-not $SkipInstall) { & $npm install --no-fund --no-audit; if ($LASTEXITCODE -ne 0) { throw "npm install failed" } }
  & $npm run check; if ($LASTEXITCODE -ne 0) { throw "Desktop integrity gate failed" }
  $arches = if ($Arch -eq "both") { @("x64", "arm64") } else { @($Arch) }
  foreach ($a in $arches) {
    & $npm exec -- electron-builder --win portable nsis "--$a"
    if ($LASTEXITCODE -ne 0) { throw "electron-builder failed for $a" }
  }
} finally { Pop-Location }
$Release = Join-Path $Root "releases\desktop"
New-Item -ItemType Directory -Force $Release | Out-Null
Get-ChildItem (Join-Path $Desktop "dist") -File | Where-Object { $_.Extension -in ".exe", ".yml", ".blockmap" } | Copy-Item -Destination $Release -Force
$files = Get-ChildItem $Release -File | ForEach-Object { @{ name=$_.Name; bytes=$_.Length; sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower() } }
@{ schema="pocket.desktop.release.v3"; version=(Get-Content (Join-Path $Desktop "package.json") -Raw | ConvertFrom-Json).version; arch=$Arch; generated_at=(Get-Date).ToUniversalTime().ToString("o"); files=@($files) } | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $Release "desktop-release.json") -Encoding UTF8
Write-Host "POCKET_DESKTOP_RELEASE_READY $Release" -ForegroundColor Green
