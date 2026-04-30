"""Phase 11E: Test production environment protection"""
import sys
sys.path.insert(0, ".")
from app.executor_v2.env_guard import EnvGuard

tests = [
    # (base_url, env_name, method, path, summary, force, expected_allowed)
    # Dev environment - all allowed
    ("https://dev-recycle.szhibu.com", "dev", "POST", "/purchaseOrder/save", "保存", False, True),
    ("https://dev-recycle.szhibu.com", "dev", "POST", "/delete", "删除", False, True),
    # Production - high risk blocked
    ("https://prod-recycle.szhibu.com", "production", "POST", "/purchaseOrder/save", "保存", False, False),
    ("https://recycle.szhibu.com", "生产环境", "POST", "/delete", "删除", False, False),
    ("https://recycle.szhibu.com", "生产环境", "POST", "/cancel", "取消", False, False),
    # Production - medium needs confirmation
    ("https://prod-recycle.szhibu.com", "prod", "POST", "/export/order", "导出", False, False),
    ("https://prod-recycle.szhibu.com", "prod", "POST", "/export/order", "导出", True, True),
    # Production - low allowed
    ("https://prod-recycle.szhibu.com", "production", "POST", "/basic/basicCurrency/page", "分页", False, True),
    ("https://prod-recycle.szhibu.com", "production", "POST", "/basic/basicCurrency/list", "列表", False, True),
]

all_pass = True
for base_url, env_name, method, path, summary, force, expected in tests:
    allowed, risk, msg = EnvGuard.check_permission(
        base_url=base_url, method=method, path=path,
        summary=summary, env_name=env_name, force=force,
    )
    ok = "PASS" if allowed == expected else "FAIL"
    if ok == "FAIL":
        all_pass = False
    prod = "PROD" if EnvGuard.is_production(base_url, env_name) else "DEV "
    print(f"  [{ok}] {prod} {risk:6} force={force} allowed={allowed} | {method} {path} ({summary})")
    if msg:
        print(f"         => {msg[:80]}")

print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
