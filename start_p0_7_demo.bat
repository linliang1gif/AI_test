@echo off
chcp 65001 >nul
echo ========================================
echo P0-7 Swagger 接入工作台 - 快速启动
echo ========================================
echo.

echo [1/3] 检查环境...
where py >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

echo ✅ Python 和 Node.js 已安装
echo.

echo [2/3] 验证 P0-7 状态...
py verify_p0_7_status.py
if %errorlevel% neq 0 (
    echo ❌ P0-7 验证失败
    pause
    exit /b 1
)
echo.

echo [3/3] 启动说明
echo ========================================
echo.
echo 请按以下步骤启动服务：
echo.
echo 1. 启动后端（在当前窗口）：
echo    cd ai-test-platform
echo    py backend_api_server.py
echo.
echo 2. 启动前端（在新窗口）：
echo    cd ai-test-platform\frontend
echo    npm run dev
echo.
echo 3. 访问工作台：
echo    http://localhost:5173/swagger-workbench
echo.
echo ========================================
echo.
echo 按任意键启动后端服务...
pause >nul

cd ai-test-platform
py backend_api_server.py
