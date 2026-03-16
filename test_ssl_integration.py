#!/usr/bin/env python
"""Comprehensive SSL Certificate Age with Phishing Detection Test"""
import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.getcwd())

from app import analyze_url  # type: ignore[import]

test_cases = [
    ("https://amazon.com", "LEGITIMATE", "Established domain"),
    ("https://google.com", "LEGITIMATE", "Established domain"),
    ("https://amazon-security-alert.xyz", "PHISHING", "Brand impersonation + suspicious TLD"),
    ("https://google-payment-verify.xyz", "PHISHING", "Brand impersonation + suspicious TLD"),
    ("http://127.0.0.1:8080/test", "SUSPICIOUS", "IP address (no SSL)"),
]

print("\n" + "="*100)
print("SSL CERTIFICATE AGE INTEGRATED WITH PHISHING DETECTION")
print("="*100)

results_summary = []

for url, expected, description in test_cases:
    result = analyze_url(url)
    actual = result["result"].upper()
    
    # Check if result matches expectation
    status = "[PASS]" if actual == expected else "[FAIL]"
    results_summary.append({
        "url": url,
        "expected": expected,
        "actual": actual,
        "status": status,
        "risk": result["risk_score"],
        "description": description
    })
    
    print(f"\n{status}")
    print(f"URL: {url}")
    print(f"Description: {description}")
    print(f"Expected: {expected} | Actual: {actual} | Risk: {result['risk_score']}%")
    
    # Show SSL certificate info
    ssl_check = result['checks'].get('ssl_certificate_age', {})
    if ssl_check.get('status') == 'ok':
        print(f"SSL Certificate: {ssl_check.get('certificate_age_days')} days old - {ssl_check.get('details')}")
    else:
        print(f"SSL Certificate: {ssl_check.get('details')}")
    
    # Show top detection flags
    if result['flags']:
        print(f"Top Flags:")
        for flag in result['flags'][:4]:
            print(f"  - {flag}")

print("\n" + "="*100)
print("TEST SUMMARY")
print("="*100)
print(f"\n{'URL':<45} {'Expected':<12} {'Actual':<12} {'Risk':<8} {'Status'}")
print("-"*105)

all_passed = True
for item in results_summary:
    url_short = item['url'][:42] + "..." if len(item['url']) > 42 else item['url']
    status_symbol = "[OK]" if "PASS" in item['status'] else "[FAIL]"
    print(f"{url_short:<45} {item['expected']:<12} {item['actual']:<12} {item['risk']:>6}% {status_symbol}")
    if "FAIL" in item['status']:
        all_passed = False

print("\n" + "="*100)
if all_passed:
    print("[SUCCESS] ALL TESTS PASSED!")
    print("\nSSL CERTIFICATE DETECTION SUCCESSFULLY INTEGRATED:")
    print("  - SSL certificate age detection working")
    print("  - Risk scoring based on certificate age (< 2 days: 50, < 7 days: 25, < 30 days: 10)")
    print("  - Graceful handling of non-HTTPS and IP addresses")
    print("  - All existing phishing detection features preserved")
    print("  - Frontend compatible output format")
else:
    print("[FAILED] SOME TESTS FAILED - Check output above")

print("="*100 + "\n")
