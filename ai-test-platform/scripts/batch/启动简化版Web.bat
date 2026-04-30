@echo off
chcp 65001 >nul
echo ========================================
echo   AI Test Platform 简化版Web服务器
echo ========================================
echo.

echo [检查] 正在检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [检查] Python环境正常
echo.

echo [检查] 正在检查依赖包...
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 正在安装FastAPI...
    pip install fastapi uvicorn
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [检查] 依赖包正常
echo.

echo [启动] 正在启动简化版Web服务器...
echo [访问] 请在浏览器中打开: http://localhost:8080
echo [说明] 这是简化版，确保基本功能正常
echo [提示] 按 Ctrl+C 停止服务器
echo.
echo ========================================
echo.

python simple_web_server.py

echo.
echo 服务器已停止
pause