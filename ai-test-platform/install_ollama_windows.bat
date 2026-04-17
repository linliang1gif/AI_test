@echo off
echo ========================================
echo     Ollama Windows 安装脚本
echo     适用于无显卡的CPU运行
echo ========================================
echo.

echo 1. 正在检查系统环境...
echo    - 操作系统: Windows
echo    - 运行模式: CPU (无显卡)
echo    - 推荐内存: 8GB+
echo.

echo 2. 下载Ollama安装包...
echo    请手动执行以下步骤:
echo.
echo    方法1 - 官网下载 (推荐):
echo    1) 打开浏览器访问: https://ollama.ai
echo    2) 点击 "Download for Windows"
echo    3) 下载 OllamaSetup.exe
echo    4) 双击运行安装程序
echo.
echo    方法2 - 命令行安装:
echo    如果你有 winget，可以运行:
echo    winget install Ollama.Ollama
echo.

pause

echo 3. 验证安装...
echo    安装完成后，Ollama会自动启动服务
echo    你可以在系统托盘看到Ollama图标
echo.

echo 4. 测试连接...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% == 0 (
    echo    ✅ Ollama服务运行正常
) else (
    echo    ❌ Ollama服务未运行，请检查安装
    echo    提示: 安装后需要重启或手动启动Ollama
)

echo.
echo 5. 下载推荐模型 (CPU优化版本)...
echo    为了在CPU上获得更好的性能，我们推荐较小的模型:
echo.
echo    基础模型 (推荐):
echo    ollama pull qwen2.5:1.5b
echo.
echo    代码专用模型:
echo    ollama pull deepseek-coder:1.3b
echo.
echo    通用模型:
echo    ollama pull llama3.2:1b
echo.

echo ========================================
echo 安装完成后请运行: python test_ollama_integration.py
echo ========================================
pause