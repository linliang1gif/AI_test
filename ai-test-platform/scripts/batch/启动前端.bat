@echo off
echo ========================================
echo 启动前端开发服务器
echo ========================================
echo.

cd frontend

echo 检查 node_modules...
if not exist "node_modules" (
    echo node_modules 不存在,正在安装依赖...
    call npm install
)

echo.
echo 启动开发服务器...
echo 访问地址: http://localhost:5173
echo.
echo 按 Ctrl+C 停止服务器
echo.

call npm run dev

pause
