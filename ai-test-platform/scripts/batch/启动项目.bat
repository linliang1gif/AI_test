@echo off
chcp 65001 >nul
echo ====================================================================================================
echo 🚀 AI测试平台 - 完整项目启动
echo ====================================================================================================
echo 📋 平台特性:
echo    🎨 现代SaaS风格界面 (Postman/Linear/Notion设计)
echo    🧠 AI驱动的测试生成和分析
echo    📊 实时数据监控和可视化
echo    🔄 完整的测试生命周期管理
echo    🛠️ 自动化脚本生成和执行
echo    📈 智能测试报告和分析
echo    🔍 API接口探索和测试
echo    ⚡ 实时测试执行监控
echo ====================================================================================================
echo.

echo 🔍 检查系统依赖...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    ❌ Python未安装或不在PATH中
    pause
    exit /b 1
) else (
    echo    ✅ Python已安装
)

npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    ❌ npm未安装或不在PATH中
    pause
    exit /b 1
) else (
    echo    ✅ npm已安装
)

echo.
echo 📦 检查前端依赖...
if not exist "frontend\node_modules" (
    echo    📥 安装前端依赖...
    cd frontend
    npm install
    if %errorlevel% neq 0 (
        echo    ❌ 前端依赖安装失败
        pause
        exit /b 1
    )
    cd ..
    echo    ✅ 前端依赖安装成功
) else (
    echo    ✅ 前端依赖已存在
)

echo.
echo 🚀 启动服务...
echo 🔧 启动后端API服务...
start "AI测试平台-后端" cmd /k "py backend_api_server.py"
echo    ✅ 后端服务启动成功
echo    📍 API地址: http://127.0.0.1:8081
echo    📖 API文档: http://127.0.0.1:8081/docs

timeout /t 3 /nobreak >nul

echo 🎨 启动前端开发服务...
cd frontend
start "AI测试平台-前端" cmd /k "npm run dev"
echo    ✅ 前端服务启动成功
echo    🌐 前端地址: http://localhost:3000
cd ..

echo.
echo ⏳ 等待服务启动...
timeout /t 5 /nobreak >nul

echo.
echo ====================================================================================================
echo 🌟 AI测试平台 - 项目启动完成
echo ====================================================================================================
echo.
echo 🌐 访问地址:
echo    📱 前端界面: http://localhost:3000
echo       • 现代SaaS风格设计
echo       • 8个核心功能模块
echo       • 实时数据监控
echo       • 中文本地化界面
echo.
echo    🔧 后端API: http://127.0.0.1:8081
echo       • RESTful API接口
echo       • 实时数据处理
echo       • Swagger文档: http://127.0.0.1:8081/docs
echo.
echo 🎯 核心功能模块:
echo    1. 仪表板: 实时统计、测试趋势、系统状态监控
echo    2. 项目管理: 项目创建、配置管理、测试覆盖率
echo    3. 接口管理: Swagger解析、API测试、接口文档
echo    4. 测试用例: AI生成用例、用例管理、执行跟踪
echo    5. 自动化脚本: pytest脚本生成、代码查看、执行管理
echo    6. 测试执行: 实时监控、进度跟踪、结果统计
echo    7. 测试报告: 报告生成、数据可视化、导出功能
echo    8. AI分析中心: 智能分析、AI代理工作流、错误诊断
echo.
echo 🚀 AI驱动特性:
echo    🧠 智能测试用例生成
echo    🔄 自动化脚本生成
echo    📊 实时测试分析
echo    🛠️ 自动错误修复建议
echo    📈 智能测试报告
echo    🔍 API接口智能探索
echo.
echo 💡 使用指南:
echo    1. 访问 http://localhost:3000 开始使用
echo    2. 点击侧边栏菜单探索不同功能
echo    3. 在项目管理中创建新项目
echo    4. 使用接口管理导入Swagger文档
echo    5. 通过AI生成测试用例和脚本
echo    6. 监控测试执行和查看报告
echo.
echo 🌐 自动打开浏览器...
start http://localhost:3000
echo    ✅ 浏览器已打开
echo.
echo ====================================================================================================
echo 💡 提示: 
echo    • 前端和后端服务已在新窗口中启动
echo    • 关闭对应的命令行窗口即可停止服务
echo    • 建议使用Chrome或Edge浏览器获得最佳体验
echo ====================================================================================================
echo.
pause