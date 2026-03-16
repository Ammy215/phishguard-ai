#!/usr/bin/env python
"""Verify SSL Certificate Age in API Response - Full Structure"""
import os
import sys
import json

os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.getcwd())

from app import app  # type: ignore[import]

# Create test client
client = app.test_client()

print("\n" + "="*100)
print("API RESPONSE STRUCTURE - SSL Certificate Age Field Verification")
print("="*100)

# Test with legitimate domain
url = "https://amazon.com"
print(f"\nTesting URL: {url}")
print("-" * 100)

response = client.post('/predict', json={"url": url})
data = response.get_json()

print("\nResponse Structure:")
print(f"  - result: {data.get('result')}")
print(f"  - risk_score: {data.get('risk_score')}")
print(f"  - ml_score: {data.get('ml_score')}")
print(f"  - rule_score: {data.get('rule_score')}")

print(f"\nChecks Available in Response:")
if 'checks' in data:
    for check_name, check_data in data['checks'].items():
        print(f"\n  Check: {check_name}")
        if isinstance(check_data, dict):
            for key, value in check_data.items():
                if isinstance(value, str) and len(str(value)) > 60:
                    print(f"    {key}: {str(value)[:60]}...")
                else:
                    print(f"    {key}: {value}")
else:
    print("  ERROR: 'checks' field not found!")

print("\n" + "="*100)
print("SSL CERTIFICATE AGE CHECK - DETAILED VIEW")
print("="*100)

if 'checks' in data and 'ssl_certificate_age' in data['checks']:
    ssl_check = data['checks']['ssl_certificate_age']
    print(f"\nSSL Certificate Age Details for {url}:")
    print(json.dumps(ssl_check, indent=2))
    print("\nStatus: [SUCCESS] SSL Certificate Age field is present and populated")
else:
    print("\nStatus: [ERROR] SSL Certificate Age field not found")

print("\n" + "="*100)
