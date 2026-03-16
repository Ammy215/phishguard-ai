#!/usr/bin/env python
import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.getcwd())

from app import analyze_url  # type: ignore[import]

test_urls = [
    'https://amazon-security-alert.xyz',
    'https://google-payment-verify.xyz',
    'https://amazon.com',
    'https://paypal-verify-account.xyz',
]

print("="*70)
print("TESTING FIXES FOR PHISHING DETECTION")
print("="*70)

for url in test_urls:
    print(f'\n{"*"*70}')
    print(f'URL: {url}')
    print(f'{"*"*70}')
    
    result = analyze_url(url)
    
    print(f'Result: {result["result"].upper()}')
    print(f'Risk Score: {result["risk_score"]}%')
    print(f'Rule Score: {result["rule_score"]}')
    print(f'ML Score: {result["ml_score"]}%')
    print(f'\nTop Detection Flags:')
    for i, flag in enumerate(result['flags'][:8], 1):
        print(f'  {i}. {flag}')
    
    # Show checks
    print(f'\nThreats Check:')
    for check_name, check_result in result['checks'].items():
        if check_result.get('risk', 0) > 0:
            print(f'  - {check_name}: {check_result.get("details", "flagged")}')

print("\n" + "="*70)
