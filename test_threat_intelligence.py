#!/usr/bin/env python3
"""
PhishGuard AI - Threat Intelligence Pipeline Test Suite

Tests all 8 threat intelligence checks and validates the pipeline.
Run this after starting the backend: python backend/app.py
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:5000"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(msg):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{msg:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def print_pass(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_fail(msg):
    print(f"{RED}✗ {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")

def print_warn(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

def test_health():
    """Test backend health check"""
    print_header("Testing Backend Health")
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print_pass(f"Backend is online")
            print_info(f"Version: {data.get('version', 'unknown')}")
            print_info(f"Engine: {data.get('engine', 'unknown')}")
            return True
        else:
            print_fail(f"Health check failed with status {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_fail("Cannot connect to backend. Is it running? (python app.py)")
        return False
    except Exception as e:
        print_fail(f"Health check error: {e}")
        return False

def test_url(url, test_name):
    """Test a URL and display all threat intelligence checks"""
    print_header(f"Testing: {test_name}")
    print_info(f"URL: {url}\n")
    
    try:
        start_time = time.time()
        resp = requests.post(
            f"{API_BASE}/predict",
            json={"url": url},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if resp.status_code != 200:
            print_fail(f"Request failed with status {resp.status_code}")
            return False
        
        data = resp.json()
        
        # Display main result
        result = data.get("result", "unknown").upper()
        risk_level = data.get("risk_level", "unknown").upper()
        confidence = data.get("confidence", 0)
        
        result_color = RED if result == "PHISHING" else GREEN
        print(f"{result_color}{BOLD}{result} - {risk_level} RISK ({confidence}%){RESET}\n")
        
        # Display scores
        print(f"  ML Score:      {data.get('ml_score', 0)}%")
        print(f"  Rule Score:    {data.get('rule_score', 0)}/100")
        print(f"  Combined:      {data.get('combined_score', 0)}%")
        print(f"  Execution:     {elapsed:.2f}s\n")
        
        # Display detection flags
        flags = data.get("flags", [])
        if flags:
            print(f"  {YELLOW}Detection Flags ({len(flags)}):${RESET}")
            for flag in flags[:5]:
                print(f"    • {flag}")
            if len(flags) > 5:
                print(f"    ... and {len(flags) - 5} more")
        print()
        
        # Test each threat intelligence check
        checks = data.get("checks", {})
        if not checks:
            print_warn("No threat intelligence checks in response")
            return False
        
        all_checks_passed = True
        check_results = []
        
        # Define expected checks
        expected_checks = [
            ("whois_age", "WHOIS Domain Age"),
            ("google_safe_browsing", "Google Safe Browsing"),
            ("phishtank", "PhishTank"),
            ("domain_similarity", "Domain Similarity"),
            ("redirects", "Redirect Detection"),
            ("shortened_url", "Shortened URL"),
            ("openphish", "OpenPhish Feed"),
            ("urlhaus", "URLHaus Malware"),
        ]
        
        print(f"{BOLD}Threat Intelligence Checks:{RESET}\n")
        
        for check_key, check_name in expected_checks:
            check = checks.get(check_key)
            if not check:
                print_fail(f"{check_name}: NOT PRESENT")
                all_checks_passed = False
                continue
            
            status = check.get("status", "unknown")
            risk = check.get("risk", 0)
            details = check.get("details", "")
            
            # Determine status color
            if status == "unavailable":
                status_color = YELLOW
                status_icon = "⊘"
            elif status == "error":
                status_color = RED
                status_icon = "✗"
            else:
                status_color = GREEN
                status_icon = "✓"
            
            # Risk color
            risk_color = RED if risk > 20 else YELLOW if risk > 10 else GREEN
            
            print(f"  {status_icon} {check_name:25} [{status_color}{status:12}{RESET}] Risk: {risk_color}{risk:2}{RESET} - {details[:50]}")
            
            check_results.append({
                "name": check_name,
                "status": status,
                "risk": risk,
                "details": details
            })
        
        print()
        return all_checks_passed
        
    except requests.exceptions.Timeout:
        print_fail("Request timed out (took >30 seconds)")
        return False
    except requests.exceptions.ConnectionError:
        print_fail("Cannot reach backend")
        return False
    except Exception as e:
        print_fail(f"Test error: {e}")
        return False

def test_suite():
    """Run full test suite"""
    print(f"\n{BOLD}{BLUE}PhishGuard AI - Threat Intelligence Test Suite{RESET}")
    print(f"{BLUE}Testing all 8 threat intelligence checks{RESET}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test health first
    if not test_health():
        print(f"\n{RED}Backend is not running. Start it with: python app.py{RESET}\n")
        return False
    
    # Test cases
    test_cases = [
        ("https://paypa1.com/login", "Brand Impersonation (PayPal) - Should flag similarity"),
        ("https://google.com", "Legitimate Site - Should return safe"),
        ("https://g00gle.com/signin", "Leet-speak Impersonation - Should detect"),
        ("https://bit.ly/phishinglink", "Shortened URL - Should detect"),
        ("https://example123456789.xyz", "Suspicious TLD - Should flag"),
    ]
    
    results = []
    for url, description in test_cases:
        passed = test_url(url, description)
        results.append({
            "url": url,
            "description": description,
            "passed": passed
        })
        time.sleep(1)  # Rate limit between tests
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}\n")
    for result in results:
        status = GREEN if result["passed"] else RED
        icon = "✓" if result["passed"] else "✗"
        print(f"  {status}{icon} {result['description']}{RESET}")
    
    print()
    if passed == total:
        print_pass("All tests passed! Threat intelligence pipeline is fully operational.")
    else:
        print_warn(f"Some tests failed. Check backend logs for [PhishGuard] messages.")
    
    print()

def test_individual_checks():
    """Test and display each check individually"""
    print_header("Individual Check Verification")
    
    url = "https://paypa1.com/login"  # URL that should trigger multiple checks
    
    try:
        resp = requests.post(
            f"{API_BASE}/predict",
            json={"url": url},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if resp.status_code != 200:
            print_fail(f"Failed to get prediction: {resp.status_code}")
            return
        
        data = resp.json()
        checks = data.get("checks", {})
        
        print(f"URL: {url}\n")
        print(f"{BOLD}Detailed Check Results:{RESET}\n")
        
        for check_name, check_data in sorted(checks.items()):
            print(f"{BOLD}{check_name}{RESET}")
            print(f"  Status:  {check_data.get('status', 'N/A')}")
            print(f"  Risk:    {check_data.get('risk', 'N/A')}")
            print(f"  Details: {check_data.get('details', 'N/A')}")
            
            # Print additional fields
            for key, value in check_data.items():
                if key not in ["status", "risk", "details"]:
                    print(f"  {key}: {value}")
            print()
        
    except Exception as e:
        print_fail(f"Error: {e}")

def main():
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--detailed":
            test_individual_checks()
        else:
            print(f"Usage: {sys.argv[0]} [--detailed]")
            print("  --detailed: Show detailed individual check results")
    else:
        test_suite()

if __name__ == "__main__":
    main()
