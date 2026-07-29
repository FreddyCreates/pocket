# Ensures POCKET has a shared basic-auth credential for the local server and tunnel scripts.

$PocketRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PocketAuthDir = Join-Path $PocketRoot ".pocket"
$PocketAuthFile = Join-Path $PocketAuthDir "access.env"
$PocketAuthNote = Join-Path $PocketAuthDir "ACCESS.txt"
$PocketAuthUser = "pocket"
$PocketAuthPassword = $null

function New-PocketAuthPassword {
  $bytes = New-Object byte[] 32
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try {
    $rng.GetBytes($bytes)
  } finally {
    $rng.Dispose()
  }
  return [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')
}

function Load-PocketAuthFile {
  param([string]$Path)
  if (-not (Test-Path $Path)) { return @{} }
  $map = @{}
  Get-Content $Path | ForEach-Object {
    if ($_ -match '^\s*([A-Z0-9_]+)=(.*)$') {
      $map[$matches[1]] = $matches[2].Trim()
    }
  }
  return $map
}

New-Item -ItemType Directory -Force -Path $PocketAuthDir | Out-Null
$envMap = Load-PocketAuthFile -Path $PocketAuthFile
if ($envMap.ContainsKey('POCKET_BASIC_AUTH_USER') -and $envMap['POCKET_BASIC_AUTH_USER']) {
  $PocketAuthUser = $envMap['POCKET_BASIC_AUTH_USER']
}
if ($envMap.ContainsKey('POCKET_BASIC_AUTH_PASSWORD') -and $envMap['POCKET_BASIC_AUTH_PASSWORD']) {
  $PocketAuthPassword = $envMap['POCKET_BASIC_AUTH_PASSWORD']
}

$created = $false
if (-not $PocketAuthPassword) {
  $PocketAuthPassword = New-PocketAuthPassword
  $created = $true
  @(
    "POCKET_BASIC_AUTH_USER=$PocketAuthUser",
    "POCKET_BASIC_AUTH_PASSWORD=$PocketAuthPassword"
  ) | Set-Content -Encoding ASCII $PocketAuthFile
}

$pair = "{0}:{1}" -f $PocketAuthUser, $PocketAuthPassword
$auth = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($pair))
$script:PocketAuthUser = $PocketAuthUser
$script:PocketAuthPassword = $PocketAuthPassword
$script:PocketAuthHeaders = @{ Authorization = "Basic $auth" }
$env:POCKET_BASIC_AUTH_USER = $PocketAuthUser
$env:POCKET_BASIC_AUTH_PASSWORD = $PocketAuthPassword

if ($created -or -not (Test-Path $PocketAuthNote)) {
  @"
POCKET access credentials
Username: $PocketAuthUser
Password: $PocketAuthPassword
Env file: $PocketAuthFile
"@ | Set-Content -Encoding ASCII $PocketAuthNote
}

if ($created) {
  Write-Host "POCKET access credential created at $PocketAuthFile" -ForegroundColor Yellow
  Write-Host "Username: $PocketAuthUser" -ForegroundColor Yellow
  Write-Host "Password: $PocketAuthPassword" -ForegroundColor Yellow
}

return [pscustomobject]@{
  User = $PocketAuthUser
  Password = $PocketAuthPassword
  File = $PocketAuthFile
}


