#!/usr/bin/env python3
import sys, os
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.getcwd())

from app import analyze_url, normalize_url  # type: ignore[import]
import logging
logging.getLogger().setLevel(logging.CRITICAL)

print("="*70)
print("IMPROVED BACKEND TEST - STRONGER PHISHING DETECTION")
print("="*70)

urls_to_test = [
    ("http://malware.testing-google.test/testing/malware/", "PHISHING"),
    ("http://testsafebrowsing.appspot.com/s/phishing.html", "PHISHING"),
    ("https://amazon.com", "SAFE"),
    ("https://google.com", "SAFE"),
]

passed = 0
failed = 0

for url, expected in urls_to_test:
    result = analyze_url(normalize_url(url))
    level = result.get('risk_level')
    score = result.get('risk_score')
    rule_score = result.get('rule_score')
    ml_score = result.get('ml_score')
    flags = result.get('flags', [])
    
    ok = level == expected
    if ok:
        passed += 1
    else:
        failed += 1
    
    status = "[PASS]" if ok else "[FAIL]"
    print(f"\n{status} {url}")
    print(f"  Expected: {expected}, Got: {level}")
    print(f"  Risk Score: {score}%, Rule Score: {rule_score}, ML Score: {ml_score}%")
    if flags:
        print(f"  Top Flags ({len(flags)}):")
        for flag in flags[:3]:
            print(f"    - {flag}")

print("\n" + "="*70)
print(f"Results: {passed} passed, {failed} failed")
print("="*70 + "\n")

sys.exit(0 if failed == 0 else 1)
