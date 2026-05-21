$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartDev = Join-Path $Root "start-dev.ps1"

Write-Host "start_all.ps1 is kept for compatibility." -ForegroundColor Yellow
Write-Host "Forwarding to start-dev.ps1..." -ForegroundColor Cyan

& $StartDev
