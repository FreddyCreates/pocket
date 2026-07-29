# POCKET platform API client — use this instead of ad-hoc python imports.
# Example:
#   .\scripts\pocket-api.ps1 capabilities
#   .\scripts\pocket-api.ps1 chat "spawn explore github"
#   .\scripts\pocket-api.ps1 campaign "host co-pilot funding story"

param(
  [Parameter(Position=0)][string]$Cmd = "capabilities",
  [Parameter(Position=1)][string]$Arg = "",
  [string]$Base = "http://127.0.0.1:8787"
)

$passFile = Join-Path $env:USERPROFILE ".pocket\ACCESS.txt"
$pass = ""
if (Test-Path $passFile) {
  $m = Select-String -Path $passFile -Pattern "Password:\s*(.+)" | Select-Object -First 1
  if ($m) { $pass = $m.Matches.Groups[1].Value.Trim() }
}
$pair = "pocket:$pass"
$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
$h = @{
  Authorization = "Basic $b64"
  "X-Pocket-Access" = $pass
  "Content-Type" = "application/json"
}

function Invoke-Pocket($Method, $Path, $BodyObj=$null) {
  $uri = "$Base$Path"
  if ($BodyObj -ne $null) {
    $body = $BodyObj | ConvertTo-Json -Depth 8 -Compress
    return Invoke-RestMethod -Uri $uri -Method $Method -Headers $h -Body $body -TimeoutSec 600
  }
  return Invoke-RestMethod -Uri $uri -Method $Method -Headers $h -TimeoutSec 120
}

switch ($Cmd.ToLower()) {
  "capabilities" { Invoke-Pocket GET "/v1/platform/capabilities" | ConvertTo-Json -Depth 6 }
  "skills" { (Invoke-Pocket GET "/v1/skills").count }
  "health" { Invoke-RestMethod -Uri "$Base/health" | ConvertTo-Json }
  "chat" {
    $t = if ($Arg) { $Arg } else { "screenshot" }
    Invoke-Pocket POST "/v1/orchestrator/chat" @{ text=$t; prompt=$t; record=$false } | ConvertTo-Json -Depth 6
  }
  "campaign" {
    $t = if ($Arg) { $Arg } else { "POCKET host co-pilot" }
    Invoke-Pocket POST "/v1/campaigns/run" @{ topic=$t; record=$true; commercial=$true } | ConvertTo-Json -Depth 6
  }
  "spawn" {
    $g = if ($Arg) { $Arg } else { "scroll and explore the screen like a user" }
    Invoke-Pocket POST "/v1/workers/spawn" @{ goal=$g; name="API"; max_steps=6 } | ConvertTo-Json -Depth 6
  }
  "observe" { Invoke-Pocket GET "/v1/vision/observe" | ConvertTo-Json -Depth 4 }
  "api" { Invoke-Pocket GET "/v1/api" | ConvertTo-Json -Depth 6 }
  "page" {
    # Full page micro-detail → symbol graph (pixels → symbols)
    $q = if ($Arg) { $Arg } else { "800" }
    Invoke-Pocket GET "/v1/vision/page?max_ui=$q&grid=5" | ConvertTo-Json -Depth 4
  }
  "stream-start" {
    Invoke-Pocket POST "/v1/vision/stream/start" @{ interval=1.5; max_ui=500 } | ConvertTo-Json -Depth 4
  }
  "stream" {
    $after = if ($Arg) { $Arg } else { "0" }
    Invoke-Pocket GET "/v1/vision/stream?after=$after" | ConvertTo-Json -Depth 4
  }
  "stream-stop" {
    Invoke-Pocket POST "/v1/vision/stream/stop" @{} | ConvertTo-Json -Depth 3
  }
  "understand" { Invoke-Pocket GET "/v1/vision/understand" | ConvertTo-Json -Depth 4 }
  "skill" {
    $sid = if ($Arg) { $Arg } else { "page_render" }
    Invoke-Pocket POST "/v1/skills/run" @{ skill=$sid; id=$sid } | ConvertTo-Json -Depth 5
  }
  "vcomp" {
    Invoke-Pocket POST "/v1/vcomp/open" @{ label="api" } | ConvertTo-Json -Depth 4
  }
  "vcomp-sense" { Invoke-Pocket POST "/v1/vcomp/sense" @{ max_ui=400 } | ConvertTo-Json -Depth 4 }
  "mission" {
    $g = if ($Arg) { $Arg } else { "fusion sense then screenshot" }
    Invoke-Pocket POST "/v1/missions/start" @{
      goal=$g
      max_hours=1
      queue=@(
        @{ action="sense" },
        @{ skill="page_render"; params=@{ max_ui=400 } },
        @{ skill="screenshot" }
      )
    } | ConvertTo-Json -Depth 5
  }
  "workflows" { Invoke-Pocket GET "/v1/workflows" | ConvertTo-Json -Depth 5 }
  "workflow" {
    $id = if ($Arg) { $Arg } else { "wf1" }
    Invoke-Pocket POST "/v1/workflows/run" @{ id=$id } | ConvertTo-Json -Depth 5
  }
  "workflow-all" {
    Invoke-Pocket POST "/v1/workflows/run" @{ all=$true } | ConvertTo-Json -Depth 4
  }
  "studio" {
    $preset = if ($Arg) { $Arg } else { "rotato_phone" }
    Invoke-Pocket POST "/v1/studio/auto" @{ title="POCKET"; subtitle="Alpha"; preset=$preset } | ConvertTo-Json -Depth 4
  }
  default {
    Write-Host "commands: health api page stream-start stream stream-stop understand skill vcomp vcomp-sense mission workflows workflow workflow-all studio chat campaign spawn observe"
  }
}
