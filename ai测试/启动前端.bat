@echo off
echo ========================================
echo 启动 AI 测试平台前端
echo ========================================
echo.

cd ai-test-platform\frontend

echo 启动前端开发服务器...
echo 访问地址: http://localhost:5173
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

npm run dev

pause
