# 检查平台状态脚本

Write-Host "================================" -ForegroundColor Cyan
Write-Host "   检查平台运行状态" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查后端
Write-Host "检查后端 (端口 8000)..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host " ✓ 运行中" -ForegroundColor Green
    }
} catch {
    Write-Host " ✗ 未运行" -ForegroundColor Red
    Write-Host "  请运行: ai测试\启动后端.bat" -ForegroundColor Yellow
}

# 检查前端
Write-Host "检查前端 (端口 5173)..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -ErrorAction Stop
    Write-Host " ✓ 运行中" -ForegroundColor Green
} catch {
    Write-Host " ✗ 未运行" -ForegroundColor Red
    Write-Host "  请运行: ai测试\启动前端.bat" -ForegroundColor Yellow
}

# 检查Token
Write-Host "检查Token配置..." -NoNewline
if (Test-Path ".env.bluedot") {
    $content = Get-Content ".env.bluedot" -Raw
    if ($content -match "BLUEDOT_TOKEN=eyJ") {
        Write-Host " ✓ 已配置" -ForegroundColor Green
    } else {
        Write-Host " ✗ 未配置" -ForegroundColor Red
    }
} else {
    Write-Host " ✗ 文件不存在" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "如果后端和前端都运行中，可以执行接入脚本：" -ForegroundColor Cyan
Write-Host "  python bluedot_platform_integration.py" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
