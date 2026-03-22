#!/usr/bin/env python
"""Test blocklist override for illegal/banned sites"""
import sys
import os

# Change to backend directory for model loading
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from app import analyze_url

test_urls = [
    'https://exoshare.com/',
    'https://exoshare.co/',
    'https://alfafile.net/',
    'https://thepiratebay.org/',
    'https://rarbg.to/',
]

for url in test_urls:
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print('='*60)
    r = analyze_url(url)
    print(f"Result: {r['result'].upper()}")
    print(f"Risk Score: {r['risk_score']}%")
    print(f"Risk Level: {r['risk_level']}")
    blocked_check = r['checks'].get('illegal_blocked_sites', {})
    print(f"Blocklist Check: {blocked_check}")
    blocklist_flags = [f for f in r['flags'] if 'Blocklist' in f or 'blocked' in f.lower()]
    if blocklist_flags:
        print(f"Blocklist Flags: {blocklist_flags}")
