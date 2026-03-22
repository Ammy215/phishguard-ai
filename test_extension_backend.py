#!/usr/bin/env python
"""Test backend API with improved URL validation"""
import sys
import os
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
os.chdir(backend_path)
sys.path.insert(0, backend_path)

import requests

test_urls = [
    'https://google.com/',
    'https://exoshare.com/',
    'https://example.com/search?q=test#results',
    'https://channel3now.com/',
]

print("Testing Backend API with Improved URL Validation\n" + "="*60)

for url in test_urls:
    try:
        r = requests.post('http://127.0.0.1:5000/predict', 
                         json={'url': url}, 
                         timeout=8)
        print(f"\nURL: {url}")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Result: {data.get('result')}, Risk: {data.get('risk_score')}%")
        else:
            print(f"Error: {r.text[:150]}")
    except Exception as e:
        print(f"{url} - ERROR: {str(e)[:80]}")
