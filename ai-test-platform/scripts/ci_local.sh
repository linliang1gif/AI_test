#!/usr/bin/env bash
set -euo pipefail

echo "======================================================"
echo "  AI Test Platform - 本地 CI 回归 + 质量门禁"
echo "======================================================"

export PYTHONIOENCODING=utf-8
export TESTING=true
export TESTING_KEY=regression-test-key-auto
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Step 1: 前端构建 ──
echo ""
echo "[Step 1/3] 前端构建检查..."
cd "$PROJECT_DIR/frontend"
npm run build || { echo "❌ 前端构建失败"; exit 1; }
echo "✅ 前端构建成功"

# ── Step 2: 运行回归测试（自动管理后端） ──
echo ""
echo "[Step 2/3] 运行回归测试..."
cd "$PROJECT_DIR"
REGRESS_RC=0
python scripts/run_regression_all.py || REGRESS_RC=$?

if [ "$REGRESS_RC" -ne 0 ]; then
    echo ""
    echo "❌ 回归测试失败 (exit code: $REGRESS_RC)"
    exit $REGRESS_RC
fi
echo "✅ 回归测试通过"

# ── Step 3: 质量门禁（可选） ──
echo ""
echo "[Step 3/3] 质量门禁检查 (可选)..."
# 如需执行质量门禁，取消下行注释并指定 suite-id:
# python scripts/ci_quality_gate.py --suite-id 1 --gate-config configs/quality_gate.json --output data/reports/ci_gate_result.json
echo "  (跳过 - 未指定 suite-id)"

echo ""
echo "======================================================"
echo "  🎉 本地 CI 全部通过"
echo "======================================================"
