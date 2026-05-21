#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retry test case generation and execution set creation for v1.2.5 iteration."""
import requests
import json
import time

BASE = "http://localhost:8000/api/v2"
ITER_ID = 4


def main():
    # 1. Check existing test cases
    r = requests.get(f"{BASE}/iterations/{ITER_ID}/test-cases")
    cases = r.json().get("test_cases", [])
    print(f"Existing test cases: {len(cases)}")

    if len(cases) == 0:
        # 2. Generate test cases (retry with timeout)
        print("\n--- Generating test cases (may take 1-2 min due to AI API) ---")
        try:
            r = requests.post(f"{BASE}/iterations/{ITER_ID}/test-cases/generate", timeout=180)
            tc = r.json()
            print(f"Generated: {tc.get('generated', 0)} test cases")
        except requests.exceptions.Timeout:
            print("TIMEOUT: test case generation took too long")
            return
        except Exception as e:
            print(f"ERROR: {e}")
            return

        # Re-fetch cases
        r = requests.get(f"{BASE}/iterations/{ITER_ID}/test-cases")
        cases = r.json().get("test_cases", [])

    # 3. Print test case summary
    print(f"\n=== {len(cases)} test cases ===")
    type_counts = {}
    for c in cases:
        ct = c.get("case_type", "unknown")
        type_counts[ct] = type_counts.get(ct, 0) + 1
        print(f"  [{ct:10s}] [{c.get('priority','?'):6s}] {c['name']}")

    print(f"\nBy type: {json.dumps(type_counts, ensure_ascii=False)}")

    # 4. Create execution sets
    print("\n--- Creating execution sets ---")
    for t in ["smoke", "iteration", "regression"]:
        try:
            r = requests.post(f"{BASE}/iterations/{ITER_ID}/execution-sets", json={"type": t})
            if r.status_code == 200:
                es = r.json()
                print(f"  {t:12s}: ID={es['id']}, cases={es['case_count']}")
            else:
                print(f"  {t:12s}: {r.status_code} {r.text[:200]}")
        except Exception as e:
            print(f"  {t:12s}: ERROR {e}")

    # 5. Get iteration report
    print("\n--- Iteration report ---")
    r = requests.get(f"{BASE}/iterations/{ITER_ID}/report")
    if r.status_code == 200:
        report = r.json()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Report failed: {r.status_code} {r.text[:200]}")

    print(f"\n=== Done. Frontend: http://localhost:3000/iterations/{ITER_ID} ===")


if __name__ == "__main__":
    main()
