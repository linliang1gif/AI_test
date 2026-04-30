@echo off
REM 安装AI测试平台依赖

echo ========================================
echo AI测试平台 - 依赖安装
echo ========================================
echo.

REM 检查虚拟环境
if exist "..\\.venv\\Scripts\\python.exe" (
    echo [1/3] 使用现有虚拟环境
    set PYTHON=..\\.venv\\Scripts\\python.exe
    set PIP=..\\.venv\\Scripts\\pip.exe
) else (
    echo [1/3] 使用系统Python
    set PYTHON=python
    set PIP=pip
)

echo.
echo [2/3] 安装依赖包...
%PIP% install -r requirements.txt

echo.
echo [3/3] 验证关键依赖...
%PYTHON% -c "import sqlalchemy; print('✅ sqlalchemy:', sqlalchemy.__version__)"
%PYTHON% -c "import fastapi; print('✅ fastapi:', fastapi.__version__)"
%PYTHON% -c "import pydantic; print('✅ pydantic:', pydantic.__version__)"

echo.
echo ========================================
echo ✅ 依赖安装完成
echo ========================================
echo.
echo 下一步:
echo   1. 初始化数据库: python init_db.py --yes
echo   2. 启动后端: python backend_api_server.py
echo.
pause
