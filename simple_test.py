#!/usr/bin/env python3
import sys, os
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.getcwd())

from app import analyze_url, normalize_url  # type: ignore[import]
import logging
logging.getLogger().setLevel(logging.CRITICAL)

urls = {
    'https://amazon.com': 'SAFE',
    'https://google.com': 'SAFE',
    'https://flipkart.com': 'SAFE',
    'https://secure-amazon-login.xyz': 'PHISHING',
    'https://paypal-security-alert.net': 'PHISHING',
}

for url, expected in urls.items():
    result = analyze_url(normalize_url(url))
    level = result.get('risk_level')
    score = result.get('risk_score')
    rule = result.get('rule_score')
    ok = 'OK' if level == expected else 'FAIL'
    print(f'[{ok}] {url}: {level} (score: {score}%, rule: {rule})')
