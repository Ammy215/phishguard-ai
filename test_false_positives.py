#!/usr/bin/env python3
"""
Test script to verify that legitimate domains are not flagged as phishing
after the false positive fixes.
"""

import sys
import os

# Change to backend directory so relative paths work
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from app import analyze_url, normalize_url  # type: ignore[import]

# Test URLs - legitimate domains that were causing false positives
TEST_URLS = [
    "https://amazon.com",
    "https://google.com",
    "https://flipkart.com",
    "https://myntra.com",
    "https://chat.openai.com",
    "https://paypal.com",
    "https://facebook.com",
    "https://instagram.com",
    "https://microsoft.com",
    "https://apple.com",
    "https://netflix.com",
]

# Known phishing URLs to ensure we still catch bad sites
PHISHING_URLS = [
    "https://secure-amazon-login.xyz",  # Typosquatting
    "https://paypal-security-alert.net",  # Impersonation
    "https://amaz0n.com",  # Leet-speak variant
    "http://192.168.1.1/admin",  # IP address
]

def test_legitimate_urls():
    """Test that legitimate domains are classified as SAFE."""
    print("\n" + "="*70)
    print("TESTING LEGITIMATE DOMAINS (should be SAFE)")
    print("="*70)
    
    all_passed = True
    for url in TEST_URLS:
        normalized = normalize_url(url)
        result = analyze_url(normalized)
        
        risk_level = result.get("risk_level", "UNKNOWN")
        is_safe = risk_level == "SAFE"
        confidence = result.get("confidence", 0)
        
        status = "[PASS]" if is_safe else "[FAIL]"
        print(f"\n{status} - {url}")
        print(f"  Risk Level: {risk_level}")
        print(f"  Confidence: {confidence}%")
        print(f"  ML Score: {result.get('ml_score', 0)}%")
        print(f"  Rule Score: {result.get('rule_score', 0)}")
        
        if result.get("flags"):
            print(f"  Flags triggered ({len(result['flags'])}):")
            for flag in result["flags"][:5]:
                print(f"    - {flag}")
        
        if not is_safe:
            all_passed = False
            print(f"  WARNING: Expected SAFE but got {risk_level}")
    
    return all_passed


def test_phishing_urls():
    """Test that phishing domains are still detected."""
    print("\n" + "="*70)
    print("TESTING PHISHING DOMAINS (should be PHISHING or SUSPICIOUS)")
    print("="*70)
    
    all_passed = True
    for url in PHISHING_URLS:
        normalized = normalize_url(url)
        result = analyze_url(normalized)
        
        risk_level = result.get("risk_level", "UNKNOWN")
        is_dangerous = risk_level in ["PHISHING", "SUSPICIOUS"]
        confidence = result.get("confidence", 0)
        
        status = "[PASS]" if is_dangerous else "[FAIL]"
        print(f"\n{status} - {url}")
        print(f"  Risk Level: {risk_level}")
        print(f"  Confidence: {confidence}%")
        print(f"  ML Score: {result.get('ml_score', 0)}%")
        print(f"  Rule Score: {result.get('rule_score', 0)}")
        
        if result.get("flags"):
            print(f"  Flags triggered ({len(result['flags'])}):")
            for flag in result["flags"][:5]:
                print(f"    - {flag}")
        
        if not is_dangerous:
            all_passed = False
            print(f"  WARNING: Expected PHISHING/SUSPICIOUS but got {risk_level}")
    
    return all_passed


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHISHGUARD AI - FALSE POSITIVE FIX VALIDATION")
    print("="*70)
    
    legitimate_ok = test_legitimate_urls()
    phishing_ok = test_phishing_urls()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Legitimate URLs: {'[PASS] ALL PASSED' if legitimate_ok else '[FAIL] SOME FAILED'}")
    print(f"Phishing URLs:   {'[PASS] ALL PASSED' if phishing_ok else '[FAIL] SOME FAILED'}")
    print("="*70 + "\n")
    
    sys.exit(0 if (legitimate_ok and phishing_ok) else 1)
