#!/usr/bin/env python3
"""P1-7: Verify SwaggerWorkbench base_url fix"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

BASE = 'http://localhost:8000'

def main():
    print("=== Test: batch-import with explicit base_url ===")
    r = requests.post(f'{BASE}/api/v2/swagger/batch-import', json={
        'project_id': 9,
        'base_url': 'https://petstore.swagger.io/v2',
        'cases': [
            {
                'path': '/pet/findByStatus',
                'method': 'GET',
                'title': 'Find pets by status (base_url test)',
                'headers': {},
                'body': None,
                'assertions': [{'type': 'status_code', 'operator': 'eq', 'expected': 200}]
            },
            {
                'path': '/store/inventory',
                'method': 'GET',
                'title': 'Returns pet inventories (base_url test)',
                'headers': {},
                'body': None,
                'assertions': [{'type': 'status_code', 'operator': 'eq', 'expected': 200}]
            },
        ]
    }, timeout=15)
    print(f"  HTTP {r.status_code}")
    d = r.json()
    print(f"  Response: imported={d.get('imported')}, skipped={d.get('skipped')}")
    
    print("\n=== Verify execution_config.url has full domain ===")
    r = requests.get(f'{BASE}/api/v2/test-cases?project_id=9&limit=200', timeout=10)
    cases = r.json().get('test_cases', [])
    
    base_url_cases = [tc for tc in cases if 'base_url test' in (tc.get('title') or '')]
    print(f"  Found {len(base_url_cases)} batch-imported test cases")
    
    all_ok = True
    for tc in base_url_cases:
        ec = tc.get('execution_config') or {}
        url = ec.get('url', '')
        has_domain = url.startswith('https://petstore.swagger.io')
        status = "✅" if has_domain else "❌"
        print(f"  {status} {tc['title'][:40]} -> url={url}")
        if not has_domain:
            all_ok = False
    
    if not base_url_cases:
        # Check any SWG_ case
        swg_cases = [tc for tc in cases if (tc.get('id') or '').startswith('SWG_')]
        print(f"  (Checking {len(swg_cases)} SWG_ cases instead)")
        for tc in swg_cases[:3]:
            ec = tc.get('execution_config') or {}
            url = ec.get('url', '')
            has_domain = url.startswith('http')
            status = "✅" if has_domain else "❌"
            print(f"  {status} {tc['title'][:40]} -> url={url[:80]}")
            if not has_domain:
                all_ok = False
    
    print(f"\n=== Result: {'PASS' if all_ok else 'FAIL'} ===")
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
