@echo off
chcp 65001 >nul
echo ========================================
echo    AI测试平台 - 一键重启
echo ========================================
echo.

echo 正在停止所有服务...
echo.

REM 停止占用端口8000的进程（后端）
echo 停止后端服务（端口8000）...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 找到进程: %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM 停止占用端口5173的进程（前端）
echo 停止前端服务（端口5173）...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    echo 找到进程: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ✅ 服务已停止
echo.
timeout /t 2 >nul

echo ========================================
echo    启动后端服务
echo ========================================
echo.

cd ai-test-platform
start "AI测试平台-后端" cmd /k "py backend_api_server.py"

echo 等待后端启动...
timeout /t 5 >nul

echo.
echo ========================================
echo    启动前端服务
echo ========================================
echo.

cd frontend
start "AI测试平台-前端" cmd /k "npm run dev"

echo.
echo ========================================
echo    启动完成！
echo ========================================
echo.
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:5173
echo.
echo 等待10秒后自动打开浏览器...
timeout /t 10 >nul

start http://localhost:5173

echo.
echo 提示:
echo - 后端窗口标题: AI测试平台-后端
echo - 前端窗口标题: AI测试平台-前端
echo - 关闭这些窗口即可停止服务
echo.
pause
