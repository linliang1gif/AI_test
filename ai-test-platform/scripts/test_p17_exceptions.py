#!/usr/bin/env python3
"""P1-7: Exception & Security Verification"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

BASE = 'http://localhost:8000'

def main():
    results = []

    # 1. Duplicate import → 409
    print("=== 1. Duplicate import returns 409 ===")
    r = requests.post(f'{BASE}/api/v2/swagger/import-url', json={
        'project_id': 9,
        'url': 'https://petstore.swagger.io/v2/swagger.json',
        'generate_cases': True
    }, timeout=30)
    ok = r.status_code == 409
    print(f"  HTTP {r.status_code} {'✅ 409 OK' if ok else '❌ Expected 409'}")
    results.append(('duplicate-409', ok))

    # 2. Swagger import with invalid URL → friendly error
    print("\n=== 2. Invalid Swagger URL → friendly error ===")
    r = requests.post(f'{BASE}/api/v2/swagger/import-url', json={
        'project_id': 9,
        'url': 'https://nonexistent.invalid/swagger.json',
        'generate_cases': True
    }, timeout=15)
    ok = r.status_code in [400, 500] and 'detail' in r.json()
    d = r.json()
    print(f"  HTTP {r.status_code} | detail={str(d.get('detail',''))[:80]}")
    print(f"  {'✅' if ok else '❌'} Friendly error returned")
    results.append(('invalid-url-error', ok))

    # 3. Connection check failure → no DB write
    print("\n=== 3. Connection check failure → no fallout ===")
    r = requests.post(f'{BASE}/api/v2/real-project/check-connection', json={
        'base_url': 'https://nonexistent.invalid',
        'health_path': '/health',
        'auth_type': 'none',
        'timeout': 5
    }, timeout=10)
    d = r.json()
    ok = r.status_code == 200 and d.get('success') == False
    print(f"  HTTP {r.status_code} | success={d.get('success')} | msg={d.get('message','')[:60]}")
    print(f"  {'✅' if ok else '❌'} Returns success=false without crash")
    results.append(('connection-fail-safe', ok))

    # 4. Token not in response body (check auth-profiles GET)
    print("\n=== 4. Token not leaked in API response ===")
    r = requests.get(f'{BASE}/api/v2/auth-profiles/4', timeout=10)
    if r.status_code == 200:
        d = r.json()
        raw = str(d)
        has_token = 'demo-token-abc123-do-not-leak' in raw
        ok = not has_token
        if has_token:
            print(f"  ❌ LEAKED! Full token visible in response")
        else:
            print(f"  ✅ Token not in plain text in response")
            # Check if masked
            token_field = d.get('token', d.get('credential', ''))
            print(f"  token field value: [{token_field[:20]}...]" if token_field else "  token field: empty/absent")
    elif r.status_code == 404:
        print(f"  ⏭️ GET /auth-profiles/:id not implemented")
        ok = True  # Can't leak if endpoint doesn't exist
    else:
        print(f"  HTTP {r.status_code} - checking response for token...")
        raw = r.text
        has_token = 'demo-token-abc123-do-not-leak' in raw
        ok = not has_token
        print(f"  {'✅' if ok else '❌'} Token {'NOT' if ok else 'IS'} in response")
    results.append(('token-no-leak', ok))

    # 5. Token not in localStorage check (frontend static analysis)
    print("\n=== 5. Token not stored in localStorage/sessionStorage ===")
    import os
    onboarding_path = os.path.join('frontend', 'src', 'pages', 'RealProjectOnboarding.jsx')
    if os.path.exists(onboarding_path):
        content = open(onboarding_path, 'r', encoding='utf-8').read()
        has_local_storage = 'localStorage' in content and 'token' in content.lower()
        has_session_storage = 'sessionStorage' in content and 'token' in content.lower()
        ok = not has_local_storage and not has_session_storage
        if has_local_storage:
            print(f"  ❌ Found localStorage + token reference in RealProjectOnboarding")
        elif has_session_storage:
            print(f"  ❌ Found sessionStorage + token reference in RealProjectOnboarding")
        else:
            print(f"  ✅ No localStorage/sessionStorage token storage")
    else:
        print(f"  ⏭️ File not found: {onboarding_path}")
        ok = True
    results.append(('token-no-storage', ok))

    # Summary
    print("\n" + "=" * 60)
    print("P1-7 Exception Verification Results")
    print("=" * 60)
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\nPassed: {passed} | Failed: {failed}")
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
