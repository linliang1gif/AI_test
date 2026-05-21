# -*- coding: utf-8 -*-
"""本地预览 finding -> TAPD bug 转换效果（不真推 TAPD）"""
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from services.tapd_service import finding_to_tapd_bug  # noqa: E402

REPORT_ID = sys.argv[1] if len(sys.argv) > 1 else "rpt_ebc532452984"
FINDING_IDS = sys.argv[2:] if len(sys.argv) > 2 else [
    "f_28aa93a2", "f_044886e4", "f_254e7085",
]

p = f"data/code_compare/reports/{REPORT_ID}.json"
d = json.loads(open(p, "r", encoding="utf-8").read())
ctx = {
    "report_id": d.get("report_id"),
    "code_snapshot_name": d.get("code_snapshot_name", ""),
}

for fid in FINDING_IDS:
    f = next((x for x in d.get("findings", []) if x.get("finding_id") == fid), None)
    if not f:
        print(f"[skip] {fid} not found")
        continue
    out = finding_to_tapd_bug(f, ctx)
    print("=" * 70)
    print(f"finding_id = {fid}  type={f.get('type')}  conf={f.get('confidence')}  risk={f.get('risk_level')}")
    print(f"TITLE   : {out['title']}")
    print(f"SEV/PRI : {out['severity']} / {out['priority']}")
    print("-" * 70)
    print(out["description"])
    print()
