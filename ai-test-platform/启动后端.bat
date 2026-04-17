@echo off
chcp 65001 >nul
echo ========================================
echo 启动AI测试平台后端服务器
echo ========================================
echo.

cd /d "%~dp0"

echo 检查Python环境...
py --version
if errorlevel 1 (
    echo ❌ Python未安装或未配置
    pause
    exit /b 1
)

echo.
echo 启动后端服务器...
echo 访问地址: http://localhost:8000
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

py backend_api_server.py

pause
