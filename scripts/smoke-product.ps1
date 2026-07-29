# POCKET v1 product smoke — local + public surfaces
$ErrorActionPreference = "Continue"
$base = "http://127.0.0.1:8787"
$pub = "https://pocket.medinatechlabs.net"
$pass = ""
$envFile = Join-Path $env:USERPROFILE ".pocket\access.env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*POCKET_BASIC_AUTH_PASSWORD=(.*)$') { $pass = $matches[1].Trim() }
  }
}
if (-not $pass -and (Test-Path (Join-Path $env:USERPROFILE ".pocket\ACCESS.txt"))) {
  $raw = Get-Content (Join-Path $env:USERPROFILE ".pocket\ACCESS.txt") -Raw
  if ($raw -match 'Password:\s*(\S+)') { $pass = $matches[1] }
  elseif ($raw -match 'POCKET_BASIC_AUTH_PASSWORD=(\S+)') { $pass = $matches[1] }
}
$pair = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("pocket:$pass"))
$h = @{ Authorization = "Basic $pair"; "X-Pocket-Access" = $pass; "Content-Type" = "application/json" }

function Hit($name, $url, $method = "GET", $body = $null, $auth = $false) {
  try {
    $params = @{ Uri = $url; Method = $method; UseBasicParsing = $true; TimeoutSec = 45 }
    if ($auth) { $params.Headers = $h }
    if ($body) { $params.Body = $body }
    $r = Invoke-WebRequest @params
    $ok = $r.StatusCode -ge 200 -and $r.StatusCode -lt 300
    $snip = if ($r.Content.Length -gt 160) { $r.Content.Substring(0,160) } else { $r.Content }
    Write-Host ("[{0}] {1} {2} {3}" -f ($(if($ok){"OK"}else{"!!"}), $name, $r.StatusCode, $snip.Replace("`n"," ")))
    return @{ ok = $ok; content = $r.Content; code = $r.StatusCode }
  } catch {
    Write-Host ("[FAIL] {0} {1}" -f $name, $_.Exception.Message)
    return @{ ok = $false; content = ""; code = 0 }
  }
}

Write-Host "=== POCKET product smoke ===" -ForegroundColor Cyan
$health = Hit "local/health" "$base/health"
Hit "local/root" "$base/"
Hit "public/health" "$pub/health"
Hit "product" "$base/v1/product" -auth $true
Hit "doctor" "$base/v1/doctor" -auth $true
Hit "status" "$base/v1/status" -auth $true
Hit "desktop/apps" "$base/v1/desktop/apps" -auth $true
Hit "web/search" "$base/v1/web/search" "POST" '{"query":"multi agent desk"}' -auth $true
Hit "nexus/status" "$base/v1/nexus/status" -auth $true
Hit "nexus/list" "$base/v1/nexus/list" "POST" '{}' -auth $true
Hit "safety" "$base/v1/safety" -auth $true
Hit "auth/me" "$base/v1/auth/me" "POST" '{}' -auth $true

# Session round-trip: desktop list
$sessBody = '{"mode":"desktop","workspace":"workspace"}'
$s = Hit "session/desktop" "$base/v1/sessions" "POST" $sessBody -auth $true
if ($s.ok) {
  try {
    $sj = $s.content | ConvertFrom-Json
    $sid = $sj.id
    if (-not $sid) { $sid = $sj.session.id }
    if ($sid) {
      Hit "msg/list-apps" "$base/v1/sessions/$sid/messages" "POST" '{"text":"list apps"}' -auth $true
      Start-Sleep -Seconds 2
      Hit "session/get" "$base/v1/sessions/$sid" -auth $true
    }
  } catch { Write-Host "[WARN] session parse: $_" }
}

Write-Host "=== done ===" -ForegroundColor Cyan
