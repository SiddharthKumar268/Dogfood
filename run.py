#!/usr/bin/env python3
"""
Official Dogfood 2026 Acceptance Checker (run.py)
Usage: python run.py [.dogfood.toml]
"""

import sys
import os
import re
import requests

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

def parse_toml(filepath):
    if tomllib:
        with open(filepath, 'rb') as f:
            return tomllib.load(f)
    
    # Fallback basic TOML parser for .dogfood.toml structure
    data = {}
    current_section = None
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            section_match = re.match(r'^\[([A-Za-z0-9_\.]+)\]$', line)
            if section_match:
                current_section = section_match.group(1)
                data[current_section] = {}
                continue
            if '=' in line and current_section:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                data[current_section][key] = val
    return data

def parse_cookie_header(header_str):
    """Parses 'Cookie: session=xyz' or 'session=xyz' into {'session': 'xyz'}"""
    if not header_str:
        return {}
    if header_str.startswith('Cookie:'):
        header_str = header_str.split('Cookie:', 1)[1].strip()
    cookies = {}
    for part in header_str.split(';'):
        if '=' in part:
            k, v = part.strip().split('=', 1)
            cookies[k.strip()] = v.strip().strip('"').strip("'")
    return cookies

def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else '.dogfood.toml'
    if not os.path.exists(config_file):
        print(f"Error: Config file '{config_file}' not found.")
        sys.exit(1)

    cfg = parse_toml(config_file)
    base_url = cfg.get('portal', {}).get('base_url', 'http://localhost:8080').rstrip('/')
    routes = cfg.get('routes', {})
    auth = cfg.get('auth', {})

    gallery_url = f"{base_url}{routes.get('gallery', '/projects')}"
    submit_url = f"{base_url}{routes.get('submit', '/projects/new')}"
    judge_scores_url = f"{base_url}{routes.get('judge_scores', '/api/judge/scores')}"
    peer_scores_url = f"{base_url}{routes.get('peer_scores', '/api/judge/scores?judge=judge_a')}"
    csv_export_url = f"{base_url}{routes.get('csv_export', '/api/export.csv')}"

    cookie_org = parse_cookie_header(auth.get('organizer', ''))
    cookie_judge_a = parse_cookie_header(auth.get('judge_a', ''))
    cookie_judge_b = parse_cookie_header(auth.get('judge_b', ''))
    cookie_part = parse_cookie_header(auth.get('participant', ''))

    results = []

    print("==================================================")
    print("      DOGFOOD 2026 ACCEPTANCE CHECKER REPORT     ")
    print("==================================================")
    print(f"Target Portal: {base_url}\n")

    # --- TIER 1 CHECKS ---
    print("[TIER 1 CHECKS]")

    # Check 1: GET gallery, no auth -> 200
    try:
        r = requests.get(gallery_url, timeout=5)
        passed = (r.status_code == 200)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] T1.1: GET gallery (no auth) -> Expected: 200, Got: {r.status_code}")
        results.append(("T1", "GET gallery (no auth)", passed, f"Status {r.status_code}"))
        gallery_text = r.text
    except Exception as e:
        print(f"  [FAIL] T1.1: GET gallery (no auth) -> Connection error: {e}")
        results.append(("T1", "GET gallery (no auth)", False, str(e)))
        gallery_text = ""

    # Check 2: Gallery body contains fixture project title
    fixture_title = "HackTrack Pro"
    found = fixture_title in gallery_text
    status = "PASS" if found else "FAIL"
    print(f"  [{status}] T1.2: Gallery body contains '{fixture_title}' -> Found: {found}")
    results.append(("T1", f"Gallery contains fixture project '{fixture_title}'", found, "Found" if found else "Not found"))

    # Check 3: POST submit as participant, event closed -> 4xx
    try:
        payload = {
            "title": "Post-Deadline Test Project",
            "summary": "Should be rejected because event is closed",
            "description": "Attempted submission after deadline",
            "track": "Web Platform"
        }
        r = requests.post(submit_url, cookies=cookie_part, json=payload, timeout=5)
        passed = (400 <= r.status_code < 500)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] T1.3: POST submit (participant, event closed) -> Expected: 4xx, Got: {r.status_code}")
        results.append(("T1", "POST submit closed event (participant)", passed, f"Status {r.status_code}"))
    except Exception as e:
        print(f"  [FAIL] T1.3: POST submit (participant, event closed) -> Connection error: {e}")
        results.append(("T1", "POST submit closed event (participant)", False, str(e)))

    # --- TIER 2 CHECKS ---
    print("\n[TIER 2 CHECKS]")

    # Check 4: GET judge_scores as judge_a -> 200
    try:
        r = requests.get(judge_scores_url, cookies=cookie_judge_a, timeout=5)
        passed = (r.status_code == 200)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] T2.1: GET judge_scores as judge_a -> Expected: 200, Got: {r.status_code}")
        results.append(("T2", "GET judge_scores (judge_a)", passed, f"Status {r.status_code}"))
    except Exception as e:
        print(f"  [FAIL] T2.1: GET judge_scores as judge_a -> Connection error: {e}")
        results.append(("T2", "GET judge_scores (judge_a)", False, str(e)))

    # Check 5: GET peer_scores as judge_b -> 401 or 403 (CRITICAL ROLE ISOLATION)
    try:
        r = requests.get(peer_scores_url, cookies=cookie_judge_b, timeout=5)
        passed = (r.status_code in [401, 403])
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] T2.2: GET peer_scores as judge_b (isolation) -> Expected: 401/403, Got: {r.status_code}")
        results.append(("T2", "GET peer_scores (judge_b -> judge_a isolation)", passed, f"Status {r.status_code}"))
    except Exception as e:
        print(f"  [FAIL] T2.2: GET peer_scores as judge_b -> Connection error: {e}")
        results.append(("T2", "GET peer_scores (judge_b -> judge_a isolation)", False, str(e)))

    # Check 6: GET judge_scores as participant -> 401 or 403
    try:
        r = requests.get(judge_scores_url, cookies=cookie_part, timeout=5)
        passed = (r.status_code in [401, 403])
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] T2.3: GET judge_scores as participant -> Expected: 401/403, Got: {r.status_code}")
        results.append(("T2", "GET judge_scores (participant forbidden)", passed, f"Status {r.status_code}"))
    except Exception as e:
        print(f"  [FAIL] T2.3: GET judge_scores as participant -> Connection error: {e}")
        results.append(("T2", "GET judge_scores (participant forbidden)", False, str(e)))

    # Check 7: GET csv_export as organizer -> 200, comma in first line
    try:
        r = requests.get(csv_export_url, cookies=cookie_org, timeout=5)
        first_line = r.text.strip().split('\n')[0] if r.text else ""
        has_comma = ',' in first_line
        passed = (r.status_code == 200 and has_comma)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] T2.4: GET csv_export as organizer -> Expected: 200 with CSV, Got: {r.status_code} (comma: {has_comma})")
        results.append(("T2", "GET csv_export (organizer with comma)", passed, f"Status {r.status_code}, comma={has_comma}"))
    except Exception as e:
        print(f"  [FAIL] T2.4: GET csv_export as organizer -> Connection error: {e}")
        results.append(("T2", "GET csv_export (organizer with comma)", False, str(e)))

    # Summary
    print("\n==================================================")
    print("                    SUMMARY                       ")
    print("==================================================")
    total_checks = len(results)
    passed_checks = sum(1 for _, _, p, _ in results)
    t1_passed = all(p for t, _, p, _ in results if t == "T1")
    t2_passed = all(p for t, _, p, _ in results if t == "T2")

    print(f"Total Checks: {passed_checks}/{total_checks} PASSED")
    print(f"Tier 1 (Core):     {'VERIFIED' if t1_passed else 'FAILED'}")
    print(f"Tier 2 (Judging):  {'VERIFIED' if t2_passed else 'FAILED'}")
    print("==================================================")

    if passed_checks == total_checks:
        print("ALL 7 ACCEPTANCE CHECKS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print(f"WARNING: {total_checks - passed_checks} check(s) failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
