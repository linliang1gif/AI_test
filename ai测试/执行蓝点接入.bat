@echo off
echo ========================================
echo 蓝点项目平台接入
echo ========================================
echo.

echo 检查后端是否运行...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [错误] 后端未启动！
    echo.
    echo 请先启动后端:
    echo   1. 双击 "启动后端.bat"
    echo   2. 等待后端启动完成
    echo   3. 再运行本脚本
    echo.
    pause
    exit /b 1
)

echo [成功] 后端已运行
echo.

echo 开始执行蓝点项目接入...
echo ========================================
echo.

cd ..
python bluedot_platform_integration.py

echo.
echo ========================================
echo 执行完成
echo ========================================
echo.

pause
