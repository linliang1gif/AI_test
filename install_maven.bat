@echo off
chcp 65001 >nul
echo ========================================
echo    Maven 自动安装工具
echo ========================================
echo.
echo 此脚本将自动安装和配置Maven
echo.
echo 需要管理员权限才能安装到系统目录
echo 请右键选择"以管理员身份运行"
echo.
pause

echo.
echo 正在启动PowerShell安装脚本...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0install_maven.ps1"

if errorlevel 1 (
    echo.
    echo ========================================
    echo 安装失败！
    echo ========================================
    echo.
    echo 请查看错误信息，或参考 MAVEN_INSTALL_GUIDE.md 手动安装
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 请关闭此窗口，重新打开PowerShell后运行:
echo mvn -version
echo.
echo 验证安装是否成功
echo.
pause
