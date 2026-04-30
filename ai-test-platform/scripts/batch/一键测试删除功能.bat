@echo off
chcp 65001 >nul
echo ========================================
echo   AI测试平台 - 删除功能测试
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] 检查后端服务状态...
py -c "import requests; requests.get('http://localhost:8000/health', timeout=2); print('✅ 后端运行中')" 2>nul
if errorlevel 1 (
    echo ❌ 后端服务未运行
    echo.
    echo 请先启动后端服务:
    echo   1. 双击运行 start_backend.bat
    echo   2. 或手动运行: py backend_api_server.py
    echo.
    pause
    exit /b 1
)

echo.
echo [2/4] 运行后端API测试...
echo ----------------------------------------
py test_delete_fix_verification.py
if errorlevel 1 (
    echo.
    echo ⚠️  后端测试失败,请检查错误信息
    pause
    exit /b 1
)

echo.
echo [3/4] 测试完成!
echo ========================================
echo.
echo ✅ 后端删除功能正常
echo.
echo [4/4] 前端测试步骤:
echo ----------------------------------------
echo 1. 清除浏览器缓存: Ctrl + Shift + R
echo 2. 访问: http://localhost:5173/test-cases
echo 3. 勾选测试用例并删除
echo 4. 验证:
echo    - 提示显示正确的删除数量
echo    - 数据从列表消失
echo    - 勾选状态被清除
echo.
echo 📝 详细文档:
echo    - DELETE_FIX_CHECKLIST.md
echo    - QUICK_DELETE_TEST.md
echo.
pause
