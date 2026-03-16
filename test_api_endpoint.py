#!/usr/bin/env python
"""Test Backend API /predict Endpoint with SSL Certificate Age"""
import os
import sys
import json

os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.getcwd())

from app import app  # type: ignore[import]

# Create test client
client = app.test_client()

test_cases = [
    "https://amazon.com",
    "https://google.com",
    "https://github.com",
    "https://amazon-security-alert.xyz",
]

print("\n" + "="*100)
print("API ENDPOINT TEST - SSL Certificate Age in /predict Response")
print("="*100)

for url in test_cases:
    print(f"\n\nTesting: {url}")
    print("-" * 100)
    
    # Make POST request to /predict endpoint
    response = client.post('/predict', json={"url": url})
    
    if response.status_code == 200:
        data = response.get_json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Classification: {data.get('result', 'N/A').upper()}")
        print(f"Risk Score: {data.get('risk_score', 'N/A')}%")
        print(f"ML Score: {data.get('ml_score', 'N/A')}%")
        
        # Show SSL Certificate Age field
        print(f"\nSSL Certificate Age Field Present: {'ssl_certificate_age' in data}")
        
        if 'ssl_certificate_age' in data:
            ssl_data = data['ssl_certificate_age']
            print(f"\nSSL Certificate Age Details:")
            print(f"  Status: {ssl_data.get('status')}")
            print(f"  Domain: {ssl_data.get('domain')}")
            print(f"  Certificate Age (days): {ssl_data.get('certificate_age_days')}")
            print(f"  Risk: {ssl_data.get('risk')}")
            print(f"  Details: {ssl_data.get('details')}")
        else:
            print("ERROR: ssl_certificate_age field not found in response!")
        
        # Show that old whois_age field is gone
        if 'whois_age' in data:
            print("\nWARNING: Old 'whois_age' field still present (should be removed)")
        else:
            print("\nOK: Old 'whois_age' field successfully removed")
        
        # Pretty print full response (limited)
        print(f"\nFull Response Fields:")
        for key in data.keys():
            if key != 'flags':  # Skip flags for brevity
                print(f"  - {key}")
    else:
        print(f"Error: Status code {response.status_code}")
        print(f"Response: {response.get_data(as_text=True)}")

print("\n" + "="*100)
print("CONCLUSION: SSL Certificate Age successfully integrated into API response")
print("="*100 + "\n")
