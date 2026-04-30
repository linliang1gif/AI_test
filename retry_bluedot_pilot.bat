@echo off
echo ========================================
echo 蓝点项目试点快速重试脚本
echo ========================================
echo.
echo 测试账号已更新为: ldsit / 654321
echo.
echo 正在执行试点...
echo.

py pilot_bluedot_secure.py

echo.
echo ========================================
echo 试点执行完成
echo ========================================
echo.
echo 查看详细报告:
echo   - bluedot_pilot_result.json
echo   - 蓝点/BLUEDOT_PILOT_EXECUTION_RESULT.md
echo.
pause
