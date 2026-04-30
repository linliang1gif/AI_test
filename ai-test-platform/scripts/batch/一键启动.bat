@echo off
echo ============================================================
echo AI Test Platform - 一键启动
echo ============================================================

cd /d "%~dp0"

echo.
echo 正在启动后端服务...
start "后端服务" cmd /k "d:\python311\python.exe backend_api_server.py"

echo 等待后端启动...
timeout /t 5 /nobreak >nul

echo.
echo 正在启动前端服务...
cd frontend
start "前端服务" cmd /k "npm run dev"

echo.
echo ============================================================
echo 启动完成!
echo ============================================================
echo.
echo 前端地址: http://localhost:3000
echo 后端地址: http://127.0.0.1:8081
echo API文档: http://127.0.0.1:8081/docs
echo.
echo 按任意键关闭此窗口...
pause >nul
