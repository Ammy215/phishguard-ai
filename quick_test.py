#!/usr/bin/env python3
"""Quick test of legitimate domains after fixes"""
import sys
import os
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.getcwd())

from app import analyze_url, normalize_url  # type: ignore[import]

# Test URLs
test_urls = {
    "https://amazon.com": "SAFE",
    "https://google.com": "SAFE",
    "https://flipkart.com": "SAFE",
    "https://myntra.com": "SAFE",
    "https://chat.openai.com": "SAFE",
    "https://secure-amazon-login.xyz": "PHISHING|SUSPICIOUS",
    "https://paypal-security-alert.net": "PHISHING|SUSPICIOUS",
}

print("="*60)
print("QUICK PHISHING TEST RESULTS")
print("="*60)

passed = 0
failed = 0

for url, expected in test_urls.items():
    normalized = normalize_url(url)
    result = analyze_url(normalized)
    risk_level = result.get("risk_level", "UNKNOWN")
    
    is_correct = any(level in risk_level for level in expected.split("|"))
    
    status = "[OK]" if is_correct else "[FAIL]"
    if is_correct:
        passed += 1
    else:
        failed += 1
        
    print(f"{status} {url}")
    print(f"     Expected: {expected}, Got: {risk_level}")
    print()

print("="*60)
print(f"Results: {passed} passed, {failed} failed")
print("="*60)

sys.exit(0 if failed == 0 else 1)
