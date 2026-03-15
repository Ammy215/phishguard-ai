#!/usr/bin/env python3
import sys, os
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.getcwd())

from app import analyze_url, normalize_url  # type: ignore[import]
import logging
logging.getLogger().setLevel(logging.CRITICAL)

print("="*70)
print("FINAL PHISHING DETECTION TEST - FALSE POSITIVE FIXES")
print("="*70)

# Legitimate domains that should be SAFE
legitimate = {
    'https://amazon.com': 'SAFE',
    'https://google.com': 'SAFE',
    'https://flipkart.com': 'SAFE',
    'https://myntra.com': 'SAFE',
    'https://chat.openai.com': 'SAFE',
    'https://paypal.com': 'SAFE',
    'https://facebook.com': 'SAFE',
    'https://microsoft.com': 'SAFE',
}

passed = 0
failed = 0

print("\n[LEGITIMATE DOMAINS]")
for url, expected in legitimate.items():
    result = analyze_url(normalize_url(url))
    level = result.get('risk_level')
    ok = 'PASS' if level == expected else 'FAIL'
    if level == expected:
        passed += 1
    else:
        failed += 1
    status = f"[{ok}]" if ok == 'PASS' else f"[{ok}]"
    print(f"  {status} {url:40s} -> {level}")

print("\n"+ "="*70)
print(f"RESULTS: {passed} passed, {failed} failed")
print("="*70 + "\n")

sys.exit(0 if failed == 0 else 1)
