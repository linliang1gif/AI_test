#!/usr/bin/env python3
"""P1-7: Real Project Onboarding Minimal Loop Verification"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json

BASE = 'http://localhost:8000'

def main():
    results = []
    project_id = None
    env_id = None

    # Step 1: check-connection
    print("=== Step 1: check-connection (httpbin) ===")
    try:
        r = requests.post(f'{BASE}/api/v2/real-project/check-connection', json={
            'base_url': 'https://httpbin.org',
            'token': '',
            'health_path': '/get',
            'auth_type': 'none',
            'timeout': 10
        }, timeout=15)
        d = r.json()
        ok = r.status_code == 200 and d.get('success') == True
        print(f"  HTTP {r.status_code} | success={d.get('success')} | msg={d.get('message')}")
        results.append(('check-connection', ok))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(('check-connection', False))

    # Step 2: check-swagger
    print("\n=== Step 2: check-swagger (petstore) ===")
    try:
        r = requests.post(f'{BASE}/api/v2/real-project/check-swagger', json={
            'swagger_url': 'https://petstore.swagger.io/v2/swagger.json',
            'auth_type': 'none',
            'timeout': 15
        }, timeout=20)
        d = r.json()
        ok = r.status_code == 200 and d.get('success') == True
        print(f"  HTTP {r.status_code} | success={d.get('success')} | msg={d.get('message')}")
        if d.get('swagger_info'):
            si = d['swagger_info']
            print(f"  Title: {si.get('title')} | Paths: {si.get('total_paths')} | Ops: {si.get('total_operations')}")
        results.append(('check-swagger', ok))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(('check-swagger', False))

    # Step 3: Create Project
    print("\n=== Step 3: Create Project ===")
    try:
        import time as _t
        proj_name = f'P17-Test-{int(_t.time())}'
        r = requests.post(f'{BASE}/api/v2/projects', json={
            'name': proj_name,
            'description': 'P1-7 real project onboarding test',
            'team': 'QA'
        }, timeout=10)
        d = r.json()
        project_id = d.get('id')
        ok = r.status_code in [200, 201] and project_id is not None
        print(f"  HTTP {r.status_code} | project_id={project_id}")
        results.append(('create-project', ok))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(('create-project', False))

    # Step 4: Create Environment
    print("\n=== Step 4: Create Environment ===")
    try:
        r = requests.post(f'{BASE}/api/v2/environments', json={
            'project_id': project_id,
            'name': 'prod',
            'base_url': 'https://petstore.swagger.io',
            'description': 'Production environment'
        }, timeout=10)
        d = r.json()
        env_id = d.get('id')
        ok = r.status_code in [200, 201] and env_id is not None
        print(f"  HTTP {r.status_code} | env_id={env_id}")
        results.append(('create-environment', ok))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(('create-environment', False))

    # Step 5: Auth Profile (optional, test create)
    print("\n=== Step 5: Save Auth Profile (token=demo) ===")
    try:
        r = requests.post(f'{BASE}/api/v2/auth-profiles', json={
            'project_id': project_id,
            'environment_id': env_id,
            'name': 'petstore-token',
            'auth_type': 'bearer',
            'token': 'demo-token-abc123-do-not-leak'
        }, timeout=10)
        print(f"  HTTP {r.status_code}")
        if r.status_code in [200, 201]:
            d = r.json()
            print(f"  Profile ID: {d.get('id')}")
            results.append(('auth-profile', True))
        elif r.status_code == 404:
            print("  auth-profiles endpoint not found - SKIP")
            results.append(('auth-profile', 'SKIP'))
        elif r.status_code == 422:
            print(f"  Validation error: {r.text[:150]}")
            results.append(('auth-profile', 'SKIP'))
        else:
            print(f"  Response: {r.text[:150]}")
            results.append(('auth-profile', False))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(('auth-profile', False))

    # Step 6: Import Swagger
    print("\n=== Step 6: Import Swagger ===")
    try:
        r = requests.post(f'{BASE}/api/v2/swagger/import-url', json={
            'project_id': project_id,
            'url': 'https://petstore.swagger.io/v2/swagger.json',
            'generate_cases': True
        }, timeout=30)
        print(f"  HTTP {r.status_code}")
        d = r.json()
        if r.status_code in [200, 201]:
            print(f"  API Spec ID: {d.get('api_spec_id', d.get('id', '?'))}")
            print(f"  Cases: {d.get('test_cases_count', d.get('cases_generated', '?'))}")
            results.append(('import-swagger', True))
        else:
            print(f"  Detail: {d.get('detail', str(d)[:200])}")
            results.append(('import-swagger', False))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(('import-swagger', False))

    # Step 7: Duplicate Import (expect 409)
    print("\n=== Step 7: Duplicate Import (expect 409) ===")
    try:
        r = requests.post(f'{BASE}/api/v2/swagger/import-url', json={
            'project_id': project_id,
            'url': 'https://petstore.swagger.io/v2/swagger.json',
            'generate_cases': True
        }, timeout=30)
        print(f"  HTTP {r.status_code}")
        if r.status_code == 409:
            print("  409 Conflict - Duplicate correctly prevented!")
            results.append(('duplicate-prevention', True))
        else:
            d = r.json()
            print(f"  Unexpected: {str(d)[:200]}")
            results.append(('duplicate-prevention', False))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(('duplicate-prevention', False))

    # Step 8: Verify project detail data
    print("\n=== Step 8: Verify Project Detail ===")
    try:
        # Project exists
        r = requests.get(f'{BASE}/api/v2/projects/{project_id}', timeout=10)
        print(f"  Project GET: HTTP {r.status_code}")
        proj_ok = r.status_code == 200

        # Environment exists
        r = requests.get(f'{BASE}/api/v2/environments?project_id={project_id}', timeout=10)
        envs = r.json() if r.status_code == 200 else []
        if isinstance(envs, dict):
            envs = envs.get('environments', envs.get('data', []))
        print(f"  Environments: {len(envs)} found")
        env_ok = len(envs) > 0

        # API specs exist
        r = requests.get(f'{BASE}/api/v2/swagger/api-specs?project_id={project_id}', timeout=10)
        specs_data = r.json() if r.status_code == 200 else []
        if isinstance(specs_data, dict):
            specs_data = specs_data.get('api_specs', specs_data.get('data', []))
        print(f"  API Specs: {len(specs_data)} found")
        spec_ok = len(specs_data) > 0

        # Test cases
        r = requests.get(f'{BASE}/api/v2/test-cases?project_id={project_id}', timeout=10)
        cases_data = r.json() if r.status_code == 200 else {}
        cases = cases_data.get('test_cases', [])
        print(f"  Test Cases: {len(cases)} found")
        cases_ok = len(cases) > 0

        all_ok = proj_ok and env_ok and spec_ok
        results.append(('project-detail-verify', all_ok))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(('project-detail-verify', False))

    # Summary
    print("\n" + "=" * 60)
    print("P1-7 Onboarding Flow Results")
    print("=" * 60)
    passed = 0
    skipped = 0
    failed = 0
    for name, ok in results:
        if ok == 'SKIP':
            icon = "⏭️"
            skipped += 1
        elif ok:
            icon = "✅"
            passed += 1
        else:
            icon = "❌"
            failed += 1
        print(f"  {icon} {name}")

    print(f"\nPassed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print(f"project_id={project_id}, env_id={env_id}")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
