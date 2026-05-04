@echo off
chcp 65001 >nul
echo ======================================================
echo   AI Test Platform - 本地 CI 回归 + 质量门禁
echo ======================================================

set PYTHONIOENCODING=utf-8
set TESTING=true
set TESTING_KEY=regression-test-key-auto

REM ── Step 1: 前端构建 ──
echo.
echo [Step 1/3] 前端构建检查...
cd /d "%~dp0\..\frontend"
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 前端构建失败，CI 终止
    exit /b 1
)
echo ✅ 前端构建成功

REM ── Step 2: 运行回归测试（自动管理后端） ──
echo.
echo [Step 2/3] 运行回归测试...
cd /d "%~dp0\.."
python scripts/run_regression_all.py
set REGRESS_RC=%ERRORLEVEL%

if %REGRESS_RC% NEQ 0 (
    echo.
    echo ❌ 回归测试失败 (exit code: %REGRESS_RC%)
    exit /b %REGRESS_RC%
)
echo ✅ 回归测试通过

REM ── Step 3: 质量门禁（可选，需要指定 suite-id） ──
echo.
echo [Step 3/3] 质量门禁检查 (可选)...
REM 如需执行质量门禁，取消下行注释并指定 suite-id:
REM python scripts/ci_quality_gate.py --suite-id 1 --gate-config configs/quality_gate.json --output data/reports/ci_gate_result.json
echo   (跳过 - 未指定 suite-id)

echo.
echo ======================================================
echo   🎉 本地 CI 全部通过
echo ======================================================
exit /b 0
