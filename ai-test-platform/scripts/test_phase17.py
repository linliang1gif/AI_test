"""Phase 17 acceptance test"""
import requests

BASE = 'http://localhost:8000'
H = {'Authorization': 'Bearer demo-token'}
results = []

def check(name, cond):
    results.append((name, cond))
    status = "PASS" if cond else "FAIL"
    print(f"  {status}: {name}")

print("=== Phase 17 Acceptance Tests ===\n")

# 1. Demo status
r = requests.get(f"{BASE}/api/v2/demo/status")
d = r.json()
check("Demo status API", r.status_code == 200)
check("Demo initialized", d["data"]["initialized"] == True)
check("Demo has 115 cases", d["data"]["test_case_count"] == 115)

# 2. Mock login
r = requests.post(f"{BASE}/api/mock/login", json={"username": "admin", "password": "123456"})
check("Mock login OK", r.status_code == 200 and r.json()["code"] == 0)

# 3. Mock 401
r = requests.get(f"{BASE}/api/mock/products")
check("Mock 401 no auth", r.status_code == 401)

# 4. Mock products list
r = requests.get(f"{BASE}/api/mock/products", headers=H)
check("Mock products list", r.status_code == 200 and r.json()["code"] == 0)

# 5. Mock 404
r = requests.get(f"{BASE}/api/mock/products/999999", headers=H)
check("Mock 404 product", r.status_code == 404)

# 6. Mock 400 missing name
r = requests.post(f"{BASE}/api/mock/products", headers=H, json={"price": 100})
check("Mock 400 missing name", r.status_code == 400)

# 7. Business error - cancel
r = requests.post(f"{BASE}/api/mock/orders/3/cancel", headers=H)
check("Mock biz error cancel", r.json()["code"] == 40001)

# 8. Bill status flow errors
r = requests.post(f"{BASE}/api/mock/payment-bills/1/approve", headers=H)
check("Mock bill draft->approve fail", r.json()["code"] == 40004)

r = requests.post(f"{BASE}/api/mock/payment-bills/4/pay", headers=H)
check("Mock bill already paid", r.json()["code"] == 40005)

# 9. Reports summary
r = requests.get(f"{BASE}/api/mock/reports/summary", headers=H)
check("Mock reports summary", r.status_code == 200 and r.json()["code"] == 0)

# 10. Governance summary
r = requests.get(f"{BASE}/api/v2/test-cases/governance-summary")
g = r.json()
check("Governance summary OK", r.status_code == 200 and g["total"] == 115)
check("Governance all governed", g["governed"] == 115)
check("Governance destructive > 0", g["destructive_count"] > 0)

# 11. Recommended sets
for preset in ["smoke", "regression", "query-safe", "failed-rerun", "p0"]:
    r = requests.get(f"{BASE}/api/v2/test-cases/recommended/{preset}")
    check(f"Recommended {preset}", r.status_code == 200)

# 12. V2 test cases
r = requests.get(f"{BASE}/api/v2/test-cases?limit=1000")
check("V2 test cases list", r.status_code == 200)

# 13. Govern endpoint
r = requests.post(f"{BASE}/api/v2/test-cases/govern", json={"force": False})
check("Govern endpoint", r.status_code == 200)

print()
passed = sum(1 for _, c in results if c)
total = len(results)
print(f"Result: {passed}/{total} passed")
if passed == total:
    print("ALL TESTS PASSED")
else:
    fails = [n for n, c in results if not c]
    print(f"FAILED: {fails}")
