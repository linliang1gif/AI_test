@echo off
echo ========================================
echo   AI Test Platform Web可视化平台启动
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.11+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] Python环境检查通过
echo.

REM 检查依赖是否安装
echo [信息] 检查依赖包...
python -c "import fastapi, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 缺少必要依赖，正在安装...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [信息] 依赖检查通过
echo.

REM 启动Web服务器
echo [启动] 正在启动AI Test Platform Web服务器...
echo [访问] 请在浏览器中打开: http://localhost:8080
echo [提示] 按 Ctrl+C 停止服务器
echo.
echo ========================================
echo.

python app/web/web_server.py

pause