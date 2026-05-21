"""Verify L1-L4 layered assertions work correctly"""
import requests, json

BACKEND = "http://localhost:8000"
BLUEDOT = "https://dev-recycle.szhibu.com/dev-api/recycle"

# 1. Generate cases with new layered assertions
r = requests.post(f"{BACKEND}/api/v2/execute/generate-from-swagger", json={
    "include_patterns": ["page", "list"],
    "exclude_patterns": ["save", "update", "delete"],
    "max_cases": 3,
})
cases = r.json()["cases"]
print("=== Generated cases with L1-L4 assertions ===")
for c in cases:
    print(f"  {c['path']}: {len(c['assertions'])} assertions")
    for a in c["assertions"]:
        print(f"    {a['type']:>15} path={a.get('path','')} exp={a.get('expected','')}")

# 2. Execute and verify business code assertion
print("\n=== Execute with L1-L4 assertions ===")
r = requests.post(f"{BACKEND}/api/v2/execute/batch", json={
    "base_url": BLUEDOT,
    "run_id": "p11-l1l4-test",
    "cases": cases,
})
data = r.json()
print(f"run_id: {data['run_id']}, summary: {data['summary']}")

for res in data["results"]:
    status = res["status"]
    title = res["case_title"]
    print(f"\n  [{status}] {title}")
    for a in res.get("assertions", []):
        icon = "V" if a["passed"] else "X"
        print(f"    [{icon}] {a['type']:>15}: exp={a.get('expected')} act={a.get('actual','')} {a.get('message','')}")

# 3. Test business code failure detection
print("\n=== Verify HTTP 200 + code!=200 => FAILED ===")
r = requests.post(f"{BACKEND}/api/v2/execute", json={
    "base_url": BLUEDOT,
    "title": "exchangeRate/list (code=10000 expected)",
    "method": "POST",
    "path": "/basic/basicExchangeRate/list",
    "body": {},
    "assertions": [
        {"type": "status_code", "expected": 200},
        {"type": "field_exists", "path": "code"},
        {"type": "field_equals", "path": "code", "expected": 200},
    ],
})
result = r.json()["result"]
print(f"  status: {result['status']}")
print(f"  HTTP: {result['response']['status_code']}")
for a in result["assertions"]:
    icon = "V" if a["passed"] else "X"
    print(f"  [{icon}] {a['type']:>15}: exp={a.get('expected')} act={a.get('actual','')} {a.get('message','')}")

if result["status"] == "failed":
    print("\n  CONFIRMED: HTTP 200 but code!=200 => status=failed")
else:
    print(f"\n  WARNING: status={result['status']} (should be failed)")
