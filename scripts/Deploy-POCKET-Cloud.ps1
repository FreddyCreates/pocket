param([string]$DatabaseId = $env:POCKET_D1_DATABASE_ID,[switch]$SkipMigrations)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Cloud = Join-Path $Root "cloudflare\pocket-cloud"
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npm) { $npm = (Get-Command npm -ErrorAction Stop).Source }
if (-not $DatabaseId) { throw "Set POCKET_D1_DATABASE_ID or pass -DatabaseId. Do not deploy a placeholder database binding." }
$Template = Get-Content (Join-Path $Cloud "wrangler.jsonc") -Raw
$Config = Join-Path $Cloud "wrangler.production.jsonc"
Set-Content $Config ($Template.Replace("REPLACE_WITH_D1_DATABASE_ID", $DatabaseId)) -Encoding UTF8
Push-Location $Cloud
try {
  & $npm install --no-fund --no-audit; if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
  & $npm run test; if ($LASTEXITCODE -ne 0) { throw "POCKET Cloud tests failed" }
  if (-not $SkipMigrations) {
    & $npm exec -- wrangler d1 migrations apply pocket-cloud --remote --config $Config
    if ($LASTEXITCODE -ne 0) { throw "D1 migrations failed" }
  }
  & $npm exec -- wrangler deploy --config $Config
  if ($LASTEXITCODE -ne 0) { throw "Worker deploy failed" }
} finally { Pop-Location }
Write-Host "POCKET_CLOUD_DEPLOYED. Confirm the Worker URL before changing existing tunnel or DNS routes." -ForegroundColor Green
