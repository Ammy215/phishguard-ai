#!/usr/bin/env python
"""Test SSL Certificate Age Detection"""
import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.getcwd())

from app import check_ssl_certificate_age, analyze_url  # type: ignore[import]

test_urls = [
    'https://amazon.com',
    'https://google.com',
    'https://github.com',
    'https://amazon-security-alert.xyz',  # Doesn't exist - will fail SSL check
    'https://chat.openai.com',
]

print("\n" + "="*80)
print("SSL CERTIFICATE AGE DETECTION TEST")
print("="*80)

for url in test_urls:
    print(f"\nTesting: {url}")
    print("-" * 80)
    
    try:
        cert_result = check_ssl_certificate_age(url)
        print(f"Status: {cert_result.get('status')}")
        print(f"Details: {cert_result.get('details')}")
        
        if cert_result.get('certificate_age_days') is not None:
            print(f"Certificate Age: {cert_result.get('certificate_age_days')} days")
            print(f"Risk Score: {cert_result.get('risk')}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

print("\n" + "="*80)
print("FULL URL ANALYSIS - Amazon Legitimate Domain")
print("="*80)

result = analyze_url('https://amazon.com')
print(f"\nURL: https://amazon.com")
print(f"Result: {result['result'].upper()}")
print(f"Risk Score: {result['risk_score']}%")
print(f"\nSSL Certificate Age Check:")
ssl_check = result['checks'].get('ssl_certificate_age', {})
print(f"  Status: {ssl_check.get('status')}")
print(f"  Details: {ssl_check.get('details')}")
print(f"  Risk: {ssl_check.get('risk')}")

print("\n" + "="*80)
