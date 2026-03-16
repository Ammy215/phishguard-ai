"""
Diagnostic script to test Google Safe Browsing API integration
Run this to debug Safe Browsing connection issues
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Try both possible env var names
API_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", os.getenv("GOOGLE_SAFE_BROWSING_KEY", "")).strip()

print("=" * 60)
print("PhishGuard Safe Browsing API Diagnostic Tool")
print("=" * 60)

# Step 1: Check if API key is loaded
print("\n[STEP 1] Checking API Key Configuration...")
if not API_KEY:
    print("❌ ERROR: API key not found!")
    print("   - Check .env file for GOOGLE_SAFE_BROWSING_API_KEY or GOOGLE_SAFE_BROWSING_KEY")
    print("   - Current .env search paths: current directory, parent directories")
    sys.exit(1)
else:
    print("✓ API key loaded successfully")
    print(f"  Key (first 10 chars): {API_KEY[:10]}...")
    print(f"  Key length: {len(API_KEY)} characters")

# Step 2: Validate API key format
print("\n[STEP 2] Validating API Key Format...")
if len(API_KEY) < 20:
    print("⚠️  WARNING: API key seems too short (expected 40+ characters)")
else:
    print("✓ API key length looks valid")

# Step 3: Test endpoint connectivity
print("\n[STEP 3] Testing Endpoint Connectivity...")
endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={API_KEY}"
print(f"  Endpoint: {endpoint[:60]}...")

try:
    # Test with a safe URL
    test_url = "https://www.google.com"
    payload = {
        "client": {"clientId": "phishguard-ai", "clientVersion": "3.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": test_url}],
        },
    }
    
    print(f"\n  Sending test request for: {test_url}")
    resp = requests.post(
        endpoint,
        json=payload,
        timeout=10,
        headers={"Content-Type": "application/json"},
        verify=True
    )
    
    print(f"  Response Status: {resp.status_code}")
    print(f"  Response Headers: {dict(resp.headers)}")
    
    if resp.status_code == 200:
        print("✓ Connection successful (HTTP 200)")
        data = resp.json() if resp.content else {}
        print(f"  Response Body: {json.dumps(data, indent=2)[:300]}")
    elif resp.status_code == 403:
        print("❌ ERROR 403 - Authentication Failed")
        print("  Possible causes:")
        print("    1. Invalid or expired API key")
        print("    2. Safe Browsing API not enabled in Google Cloud Console")
        print("    3. API key doesn't have permission for Safe Browsing")
        print("    4. Project quota exceeded")
        print(f"  Response: {resp.text[:200]}")
    elif resp.status_code == 404:
        print("❌ ERROR 404 - Endpoint Not Found")
        print(f"  Response: {resp.text[:200]}")
    else:
        print(f"❌ ERROR {resp.status_code}")
        print(f"  Response: {resp.text[:200]}")
        
except requests.exceptions.Timeout:
    print("❌ Connection Timeout (>10 seconds)")
    print("  Check: Network connectivity, firewall rules, proxy settings")
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection Error: {str(e)}")
    print("  Check: Internet connectivity, firewall, proxy settings")
except requests.exceptions.RequestException as e:
    print(f"❌ Request Error: {str(e)}")
except Exception as e:
    print(f"❌ Unexpected Error: {str(e)}")
    import traceback
    traceback.print_exc()

# Step 4: Test with known phishing URLs
print("\n[STEP 4] Testing with Known Safe/Phishing URLs...")
test_urls = [
    ("https://www.google.com", "Safe (should not be flagged)"),
    ("https://amazon.com", "Safe (should not be flagged)"),
]

for test_url, description in test_urls:
    print(f"\n  Testing: {test_url}")
    print(f"  Expected: {description}")
    
    payload = {
        "client": {"clientId": "phishguard-ai", "clientVersion": "3.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": test_url}],
        },
    }
    
    try:
        resp = requests.post(endpoint, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json() if resp.content else {}
            matches = data.get("matches", [])
            if matches:
                print(f"  ⚠️  FLAGGED: {matches}")
            else:
                print(f"  ✓ Clean")
        else:
            print(f"  ❌ HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("Diagnostic Complete")
print("=" * 60)
print("\nNext Steps:")
print("1. If API key not found: Create .env file with GOOGLE_SAFE_BROWSING_API_KEY")
print("2. If 403 error: Check Google Cloud Console for API key and permissions")
print("3. If connection error: Check firewall and network settings")
print("4. For help: https://developers.google.com/safe-browsing/v4")
