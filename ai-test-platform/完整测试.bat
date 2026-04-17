@echo off
echo ============================================================
echo AI Test Platform - 完整流程测试
echo ============================================================

cd /d "%~dp0"

d:\python311\python.exe test_workflow.py

pause
