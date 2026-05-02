#!/usr/bin/env bash
set -euo pipefail

echo "======================================================"
echo "  AI Test Platform - 本地 CI 回归"
echo "======================================================"

export PYTHONIOENCODING=utf-8
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Step 1: 前端构建 ──
echo ""
echo "[Step 1/4] 前端构建检查..."
cd "$PROJECT_DIR/frontend"
npm run build || { echo "❌ 前端构建失败"; exit 1; }
echo "✅ 前端构建成功"

# ── Step 2: 启动后端 ──
echo ""
echo "[Step 2/4] 启动后端 (TESTING=true)..."
cd "$PROJECT_DIR"
export TESTING=true
python backend_api_server.py &
BACKEND_PID=$!

# 等待后端就绪
echo "等待后端 /health ..."
for i in $(seq 1 30); do
    if python -c "import requests; r=requests.get('http://localhost:8000/health',timeout=2); exit(0 if r.ok else 1)" 2>/dev/null; then
        echo "✅ 后端就绪 (${i}s)"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "❌ 后端启动超时"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# ── Step 3: 运行回归测试 ──
echo ""
echo "[Step 3/4] 运行回归测试..."
REGRESS_RC=0
python scripts/run_regression_all.py || REGRESS_RC=$?

# ── Step 4: 清理 ──
echo ""
echo "[Step 4/4] 清理..."
kill $BACKEND_PID 2>/dev/null || true

if [ "$REGRESS_RC" -ne 0 ]; then
    echo ""
    echo "❌ CI 失败 (exit code: $REGRESS_RC)"
    exit $REGRESS_RC
fi

echo ""
echo "======================================================"
echo "  🎉 本地 CI 全部通过"
echo "======================================================"
