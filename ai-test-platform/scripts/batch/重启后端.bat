@echo off
echo 正在重启后端...

taskkill /F /IM python.exe /FI "WINDOWTITLE eq *simple_backend*" 2>nul

timeout /t 2 /nobreak >nul

cd /d "%~dp0"
start "简化后端" d:\python311\python.exe simple_backend.py

echo 后端已重启
timeout /t 3 /nobreak >nul
