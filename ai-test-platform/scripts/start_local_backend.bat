@echo off
REM AI Test Platform - 本地后端启动脚本
REM 使用虚拟环境启动后端服务

echo ========================================
echo AI Test Platform - 后端启动
echo ========================================
echo.

REM 检查虚拟环境是否存在
if not exist "venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在
    echo 请先运行: python -m venv venv
    echo 然后运行: venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

REM 检查.env文件
if not exist ".env" (
    echo [警告] .env文件不存在
    echo 将使用默认配置（Mock模式）
    echo 建议: cp .env.example .env
    echo.
)

REM 启动后端
echo [启动] 使用虚拟环境启动后端...
echo 后端地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

venv\Scripts\python.exe backend_api_server.py

pause
