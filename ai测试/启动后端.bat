@echo off
echo ========================================
echo 启动 AI 测试平台后端
echo ========================================
echo.

cd ai-test-platform

echo 检查数据库...
if not exist test_platform.db (
    echo 数据库不存在，正在初始化...
    python init_db.py
    echo.
)

echo 启动后端服务器...
echo 访问地址: http://localhost:5000
echo 健康检查: http://localhost:5000/health
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python backend_api_server.py

pause
