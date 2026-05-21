param(
  [int]$BackendPort = 8001,
  [int]$FrontendPort = 5173,
  [switch]$StatusOnly
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Frontend = Join-Path $Root "frontend"
$LogDir = Join-Path $Root "logs"
$Uvicorn = "D:\python311\Scripts\uvicorn.exe"
$Npm = "C:\Progra~1\nodejs\npm.cmd"

function Test-PortListening {
  param([int]$Port)
  $line = netstat -ano | Select-String ":$Port " | Select-String "LISTENING"
  return [bool]$line
}

function Test-HttpOk {
  param([string]$Url)
  try {
    $res = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
    return $res.StatusCode -ge 200 -and $res.StatusCode -lt 500
  } catch {
    return $false
  }
}

function Wait-Http {
  param(
    [string]$Url,
    [int]$Seconds = 30
  )
  for ($i = 1; $i -le $Seconds; $i++) {
    if (Test-HttpOk $Url) {
      return $true
    }
    Start-Sleep -Seconds 1
  }
  return $false
}

function Start-VisiblePowerShell {
  param(
    [string]$Title,
    [string]$Command
  )
  Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "`$Host.UI.RawUI.WindowTitle = '$Title'; $Command"
  )
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host "AI Test Platform dev status" -ForegroundColor Cyan
Write-Host "Root: $Root"
Write-Host ""

$backendUrl = "http://127.0.0.1:$BackendPort"
$frontendUrl = "http://127.0.0.1:$FrontendPort"
$backendListening = Test-PortListening $BackendPort
$frontendListening = Test-PortListening $FrontendPort

Write-Host ("Backend  {0}  {1}" -f $backendUrl, $(if ($backendListening) { "LISTENING" } else { "STOPPED" })) -ForegroundColor $(if ($backendListening) { "Green" } else { "Yellow" })
Write-Host ("Frontend {0}  {1}" -f $frontendUrl, $(if ($frontendListening) { "LISTENING" } else { "STOPPED" })) -ForegroundColor $(if ($frontendListening) { "Green" } else { "Yellow" })
Write-Host ""

if ($StatusOnly) {
  if ($backendListening) {
    Write-Host "Backend health: $backendUrl/health" -ForegroundColor Cyan
    try {
      Invoke-RestMethod -Uri "$backendUrl/health" -TimeoutSec 5 | ConvertTo-Json -Depth 4
    } catch {
      Write-Host "Backend health failed: $($_.Exception.Message)" -ForegroundColor Red
    }
  }
  if ($frontendListening) {
    Write-Host "Frontend: $frontendUrl/dashboard" -ForegroundColor Cyan
  }
  exit 0
}

if (-not (Test-Path $Uvicorn)) {
  throw "uvicorn not found: $Uvicorn"
}
if (-not (Test-Path $Npm)) {
  throw "npm.cmd not found: $Npm"
}
if (-not (Test-Path (Join-Path $Frontend "package.json"))) {
  throw "frontend package.json not found: $Frontend"
}

if (-not $backendListening) {
  $backendLog = Join-Path $LogDir "backend-$BackendPort.dev.log"
  $backendCmd = "Set-Location `"$Root`"; & `"$Uvicorn`" backend.app:create_app --factory --host 127.0.0.1 --port $BackendPort 2>&1 | Tee-Object -FilePath `"$backendLog`""
  Write-Host "Starting backend..." -ForegroundColor Green
  Start-VisiblePowerShell "AI Test Backend $BackendPort" $backendCmd
} else {
  Write-Host "Backend already running, skip." -ForegroundColor Yellow
}

if (-not (Wait-Http "$backendUrl/health" 40)) {
  Write-Host "Backend did not become healthy in time. Check logs/backend-$BackendPort.dev.log" -ForegroundColor Red
} else {
  Write-Host "Backend health OK." -ForegroundColor Green
}

if (-not $frontendListening) {
  $frontendLog = Join-Path $LogDir "frontend-$FrontendPort.dev.log"
  $frontendCmd = "Set-Location `"$Frontend`"; & `"$Npm`" run dev -- --host 127.0.0.1 --port $FrontendPort 2>&1 | Tee-Object -FilePath `"$frontendLog`""
  Write-Host "Starting frontend..." -ForegroundColor Green
  Start-VisiblePowerShell "AI Test Frontend $FrontendPort" $frontendCmd
} else {
  Write-Host "Frontend already running, skip." -ForegroundColor Yellow
}

if (-not (Wait-Http "$frontendUrl/dashboard" 30)) {
  Write-Host "Frontend did not become reachable in time. Check logs/frontend-$FrontendPort.dev.log" -ForegroundColor Red
} else {
  Write-Host "Frontend OK." -ForegroundColor Green
}

Write-Host ""
Write-Host "Open:" -ForegroundColor Cyan
Write-Host "  $frontendUrl/dashboard"
Write-Host "  $frontendUrl/test-cases"
Write-Host ""
Write-Host "Logs:" -ForegroundColor Cyan
Write-Host "  logs/backend-$BackendPort.dev.log"
Write-Host "  logs/frontend-$FrontendPort.dev.log"
