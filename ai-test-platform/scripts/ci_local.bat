@echo off
chcp 65001 >nul
echo ======================================================
echo   AI Test Platform - 本地 CI 回归
echo ======================================================

set PYTHONIOENCODING=utf-8

REM ── Step 1: 前端构建 ──
echo.
echo [Step 1/4] 前端构建检查...
cd /d "%~dp0\..\frontend"
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 前端构建失败，CI 终止
    exit /b 1
)
echo ✅ 前端构建成功

REM ── Step 2: 启动后端 ──
echo.
echo [Step 2/4] 启动后端 (TESTING=true)...
cd /d "%~dp0\.."
set TESTING=true
start /b python backend_api_server.py > nul 2>&1

REM 等待后端就绪
echo 等待后端 /health ...
set /a WAIT=0
:WAIT_LOOP
if %WAIT% GEQ 30 (
    echo ❌ 后端启动超时
    exit /b 1
)
timeout /t 1 /nobreak >nul
python -c "import requests; r=requests.get('http://localhost:8000/health',timeout=2); exit(0 if r.ok else 1)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    set /a WAIT=%WAIT%+1
    goto WAIT_LOOP
)
echo ✅ 后端就绪

REM ── Step 3: 运行回归测试 ──
echo.
echo [Step 3/4] 运行回归测试...
python scripts/run_regression_all.py
set REGRESS_RC=%ERRORLEVEL%

REM ── Step 4: 清理 ──
echo.
echo [Step 4/4] 清理...
taskkill /f /im python.exe >nul 2>&1

if %REGRESS_RC% NEQ 0 (
    echo.
    echo ❌ CI 失败 (exit code: %REGRESS_RC%)
    exit /b %REGRESS_RC%
)

echo.
echo ======================================================
echo   🎉 本地 CI 全部通过
echo ======================================================
exit /b 0
