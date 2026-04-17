@echo off
echo ============================================================
echo 后端服务重启脚本
echo ============================================================
echo.

echo [1/3] 检查后端进程...
tasklist | findstr /i "python" > nul
if %errorlevel% == 0 (
    echo 找到Python进程
) else (
    echo 未找到Python进程
)

echo.
echo [2/3] 尝试停止后端服务...
echo 正在查找占用8000端口的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 找到进程ID: %%a
    echo 正在终止进程...
    taskkill /F /PID %%a
    timeout /t 2 /nobreak > nul
)

echo.
echo [3/3] 启动后端服务...
cd ai-test-platform
echo 当前目录: %cd%
echo.
echo 启动后端服务器...
echo ============================================================
start "AI测试平台后端" py backend_api_server.py

echo.
echo ✅ 后端服务已在新窗口中启动
echo.
echo 等待5秒让服务启动...
timeout /t 5 /nobreak > nul

echo.
echo 验证服务是否启动...
cd ..
py check_backend_version.py

echo.
echo ============================================================
echo 重启完成
echo ============================================================
pause
