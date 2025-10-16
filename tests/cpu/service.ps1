# tests/cpu/service.ps1
# Usage (from repo root):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\tests\cpu\service.ps1 up        # start & wait until Flask is healthy
#   .\tests\cpu\service.ps1 down      # stop & remove containers + volumes
#   .\tests\cpu\service.ps1 logs      # tail logs
#   .\tests\cpu\service.ps1 restart   # force recreate + wait healthy

param(
  [ValidateSet('up','down','logs','restart')]
  [string]$Action = 'up',

  # Path to compose file
  [string]$ComposeFile = 'tests/cpu/docker-compose.yml',

  # Flask service (chromaviz)
  [string]$BaseUrl = 'http://localhost:5000',
  [string]$HealthPath = '/heartbeat',

  # Wait budget
  [int]$WaitMinutes = 5
)

$ErrorActionPreference = 'Stop'
$compose = "docker compose -f `"$ComposeFile`""

function Test-HttpHealthy {
  param([string]$Url)
  try {
    $res = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 3

    # Accept common OK shapes
    if ($res -is [string]) {
      $s = $res.ToLower()
      if ($s -eq 'ok' -or $s -eq 'healthy') { return $true }
    }
    if ($res -is [hashtable] -or $res -is [pscustomobject]) {
      if ($res.heartbeat -eq $true) { return $true }
      if ($res.status -and $res.status.ToString().ToLower() -eq 'ok') { return $true }
      if ($res.detail -and $res.detail.ToString().ToLower() -eq 'ok') { return $true }
    }

    # 200 with unknown body → treat as healthy
    return $true
  } catch {
    return $false
  }
}

function Wait-Until-Healthy {
  param([string]$Name, [string]$Url)
  Write-Host "Waiting for $Name to be healthy at $Url ..."
  $deadline = (Get-Date).AddMinutes($WaitMinutes)
  do {
    if (Test-HttpHealthy -Url $Url) {
      Write-Host "$Name healthy."
      return
    }
    Start-Sleep -Seconds 3
  } while ((Get-Date) -lt $deadline)
  throw "$Name did not become healthy within $WaitMinutes minute(s). Last tried: $Url"
}

switch ($Action) {
  'up' {
    iex "$compose up -d"
    $flaskHealthUrl = ($BaseUrl.TrimEnd('/')) + $HealthPath
    Wait-Until-Healthy -Name 'chromaviz (Flask)' -Url $flaskHealthUrl
    Write-Host "Ready. API at $BaseUrl"
  }
  'restart' {
    iex "$compose up -d --force-recreate"
    $flaskHealthUrl = ($BaseUrl.TrimEnd('/')) + $HealthPath
    Wait-Until-Healthy -Name 'chromaviz (Flask)' -Url $flaskHealthUrl
    Write-Host "Restarted. API at $BaseUrl"
  }
  'logs' {
    iex "$compose logs -f"
  }
  'down' {
    iex "$compose down -v"
    Write-Host "Service stopped and volumes removed."
  }
}
