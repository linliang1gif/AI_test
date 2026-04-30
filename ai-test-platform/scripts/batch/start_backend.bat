@echo off
echo ========================================
echo   启动AI测试平台后端服务
echo ========================================
echo.

cd /d "%~dp0"

echo 当前目录: %CD%
echo.

echo 正在启动后端服务...
py backend_api_server.py

pause
