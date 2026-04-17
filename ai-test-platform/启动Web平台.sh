#!/bin/bash

echo "========================================"
echo "  AI Test Platform Web可视化平台启动"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[错误] 未找到Python，请先安装Python 3.11+"
        echo "安装命令: sudo apt install python3 python3-pip"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "[信息] Python环境检查通过"
echo

# 检查依赖是否安装
echo "[信息] 检查依赖包..."
$PYTHON_CMD -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[警告] 缺少必要依赖，正在安装..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
fi

echo "[信息] 依赖检查通过"
echo

# 启动Web服务器
echo "[启动] 正在启动AI Test Platform Web服务器..."
echo "[访问] 请在浏览器中打开: http://localhost:8080"
echo "[提示] 按 Ctrl+C 停止服务器"
echo
echo "========================================"
echo

$PYTHON_CMD app/web/web_server.py