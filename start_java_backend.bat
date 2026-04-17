@echo off
chcp 65001 >nul
echo ========================================
echo    启动Java后端服务
echo ========================================
echo.

set JAVA_PROJECT_DIR=D:\360Downloads\蓝点\recycle-server-feature-1.2.2 (1)\recycle-server-feature-1.2.2

echo 检查Java环境...
java -version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Java环境，请先安装JDK
    pause
    exit /b 1
)
echo ✅ Java环境正常

echo.
echo 检查Maven环境...
mvn -version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Maven，请先安装Maven或使用IDEA启动
    echo.
    echo 建议：使用IntelliJ IDEA打开项目并运行主类
    pause
    exit /b 1
)
echo ✅ Maven环境正常

echo.
echo 进入项目目录...
cd /d "%JAVA_PROJECT_DIR%"
if errorlevel 1 (
    echo ❌ 项目目录不存在: %JAVA_PROJECT_DIR%
    pause
    exit /b 1
)
echo ✅ 当前目录: %CD%

echo.
echo ========================================
echo 选择启动方式:
echo 1. 快速启动（跳过测试）
echo 2. 完整编译后启动
echo 3. 仅启动（不编译）
echo ========================================
set /p choice=请选择 (1/2/3): 

if "%choice%"=="1" (
    echo.
    echo 正在快速编译...
    call mvn clean install -DskipTests
    if errorlevel 1 (
        echo ❌ 编译失败
        pause
        exit /b 1
    )
    goto start_service
)

if "%choice%"=="2" (
    echo.
    echo 正在完整编译...
    call mvn clean install
    if errorlevel 1 (
        echo ❌ 编译失败
        pause
        exit /b 1
    )
    goto start_service
)

if "%choice%"=="3" (
    goto start_service
)

echo 无效的选择
pause
exit /b 1

:start_service
echo.
echo ========================================
echo 启动服务...
echo ========================================
echo.
echo 服务信息:
echo - 端口: 8194
echo - Context Path: /recycle
echo - 完整URL: http://localhost:8194/recycle
echo.
echo 启动后可以访问:
echo - Swagger UI: http://localhost:8194/recycle/swagger-ui.html
echo - API文档: http://localhost:8194/recycle/doc.html
echo.
echo 按 Ctrl+C 可以停止服务
echo ========================================
echo.

cd recycle\recycle-business
call mvn spring-boot:run

pause
