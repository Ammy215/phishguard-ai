#!/usr/bin/env python3
import sys, os
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.getcwd())

from app import analyze_url, normalize_url  # type: ignore[import]
import logging
logging.getLogger().setLevel(logging.CRITICAL)

url = 'https://chat.openai.com'
result = analyze_url(normalize_url(url))

print(f"URL: {url}")
print(f"Risk Level: {result.get('risk_level')}")
print(f"ML Score: {result.get('ml_score')}%")
print(f"Rule Score: {result.get('rule_score')}")
print(f"Risk Score: {result.get('risk_score')}%")
print(f"\nFlags:")
for flag in result.get('flags', []):
    print(f"  - {flag}")
