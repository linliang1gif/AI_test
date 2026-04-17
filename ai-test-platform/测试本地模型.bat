@echo off
echo ============================================================
echo Ollama本地模型测试
echo ============================================================

cd /d "%~dp0"

d:\python311\python.exe test_ollama.py

pause
