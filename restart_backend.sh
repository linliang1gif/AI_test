#!/bin/bash

echo "============================================================"
echo "后端服务重启脚本"
echo "============================================================"
echo ""

echo "[1/3] 检查后端进程..."
if pgrep -f "backend_api_server.py" > /dev/null; then
    echo "找到后端进程"
    echo "正在停止..."
    pkill -f "backend_api_server.py"
    sleep 2
else
    echo "未找到运行中的后端进程"
fi

echo ""
echo "[2/3] 检查8000端口..."
if lsof -i :8000 > /dev/null 2>&1; then
    echo "端口8000仍被占用，强制释放..."
    lsof -ti :8000 | xargs kill -9
    sleep 2
fi

echo ""
echo "[3/3] 启动后端服务..."
cd ai-test-platform
echo "当前目录: $(pwd)"
echo ""
echo "启动后端服务器..."
echo "============================================================"
nohup python backend_api_server.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "后端进程ID: $BACKEND_PID"

echo ""
echo "等待5秒让服务启动..."
sleep 5

echo ""
echo "验证服务是否启动..."
cd ..
python check_backend_version.py

echo ""
echo "============================================================"
echo "重启完成"
echo "============================================================"
echo ""
echo "后端日志: ai-test-platform/backend.log"
echo "查看日志: tail -f ai-test-platform/backend.log"
