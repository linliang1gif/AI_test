@echo off
chcp 65001 >nul
echo ========================================
echo 启动后端服务器 (含触发系统)
echo ========================================
echo.

cd ai-test-platform
py backend_api_server.py

pause
