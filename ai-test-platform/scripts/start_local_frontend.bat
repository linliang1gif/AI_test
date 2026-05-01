@echo off
REM AI Test Platform - 本地前端启动脚本

echo ========================================
echo AI Test Platform - 前端启动
echo ========================================
echo.

REM 检查node_modules
if not exist "frontend\node_modules" (
    echo [错误] node_modules不存在
    echo 请先运行: cd frontend ^&^& npm install
    pause
    exit /b 1
)

REM 进入前端目录
cd frontend

REM 启动前端
echo [启动] 启动前端开发服务器...
echo 前端地址: http://localhost:5173 或 http://localhost:5174
echo.
echo 按 Ctrl+C 停止服务
echo.

npm run dev

pause
