@echo off
echo ========================================
echo 启动后端 API 服务器
echo ========================================
echo.

echo 检查数据库...
if not exist "test_platform.db" (
    echo 数据库不存在,正在初始化...
    py init_db.py --yes
)

echo.
echo 启动后端服务器...
echo API 地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务器
echo.

py backend_api_server.py

pause
