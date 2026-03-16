"""
PhishGuard AI  Flask Backend
Hybrid phishing detection engine combining a Random Forest ML model
with a 16+ rule heuristic scoring system, explainable AI chat endpoint,
URL normalization, edge-case handling, and threat intelligence checks.
"""

import os
import re
import ssl
import socket
import datetime
import logging
import threading
import time
import io
import csv
from urllib.parse import urlparse, unquote
from OpenSSL import crypto  # type: ignore[import]

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import requests
from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
#  App Setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})
app.logger.setLevel(logging.INFO)

MODEL_PATH = os.getenv("MODEL_PATH", "phish_model.joblib")
model = joblib.load(MODEL_PATH)

GOOGLE_SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", "").strip()
PHISHTANK_API_KEY = os.getenv("PHISHTANK_API_KEY", "").strip()
PHISHTANK_LOCAL_DB = os.getenv("PHISHTANK_LOCAL_DB", "phishtank.csv").strip()

# In-memory TTL cache to reduce repeated network calls.
_CACHE = {}
_CACHE_LOCK = threading.Lock()

# Global flag for background thread
_BACKGROUND_THREAD_ACTIVE = False
_BACKGROUND_THREAD = None


def _cache_get(cache_key):
    now = time.time()
    with _CACHE_LOCK:
        item = _CACHE.get(cache_key)
        if not item:
            return None
        expires_at, value = item
        if expires_at < now:
            del _CACHE[cache_key]
            return None
        return value


def _cache_set(cache_key, value, ttl_seconds):
    with _CACHE_LOCK:
        _CACHE[cache_key] = (time.time() + max(int(ttl_seconds), 1), value)


def _to_datetime(value):
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time.min)
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%b-%Y"):
            try:
                return datetime.datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None

# ---------------------------------------------------------------------------
#  Feed Management Functions
# ---------------------------------------------------------------------------
def download_phishtank_dataset():
    """Download PhishTank CSV dataset if not already present"""
    if not PHISHTANK_LOCAL_DB:
        return
    
    if os.path.exists(PHISHTANK_LOCAL_DB):
        app.logger.info("[PhishGuard] PhishTank CSV already present: %s", PHISHTANK_LOCAL_DB)
        return
    
    try:
        app.logger.info("[PhishGuard] Downloading PhishTank dataset...")
        url = "http://data.phishtank.com/data/online-valid.csv"
        resp = requests.get(url, timeout=30)
        if resp.status_code >= 400:
            raise RuntimeError("HTTP " + str(resp.status_code))
        
        with open(PHISHTANK_LOCAL_DB, "w", encoding="utf-8") as f:
            f.write(resp.text)
        
        # Count lines in CSV
        line_count = resp.text.count("\n")
        app.logger.info("[PhishGuard] PhishTank dataset downloaded: %d lines saved to %s", line_count, PHISHTANK_LOCAL_DB)
    except Exception as ex:
        app.logger.warning("[PhishGuard] Failed to download PhishTank dataset: %s", str(ex))


def refresh_feeds():
    """Refresh OpenPhish feed and PhishTank dataset"""
    try:
        app.logger.info("[PhishGuard] Starting feed refresh cycle...")
        
        # Refresh OpenPhish feed
        try:
            app.logger.info("[PhishGuard] Refreshing OpenPhish feed...")
            resp = requests.get("https://openphish.com/feed.txt", timeout=10)
            if resp.status_code >= 400:
                raise RuntimeError("HTTP " + str(resp.status_code))
            feed = {line.strip() for line in resp.text.splitlines() if line.strip()}
            with _CACHE_LOCK:
                _CACHE["openphish_feed"] = (time.time() + 60 * 60, feed)
            app.logger.info("[PhishGuard] OpenPhish feed refreshed: %d URLs", len(feed))
        except Exception as ex:
            app.logger.warning("[PhishGuard] OpenPhish feed refresh failed: %s", str(ex))
        
        # Refresh PhishTank dataset if using local
        if PHISHTANK_LOCAL_DB:
            try:
                app.logger.info("[PhishGuard] Refreshing PhishTank dataset...")
                url = "http://data.phishtank.com/data/online-valid.csv"
                resp = requests.get(url, timeout=30)
                if resp.status_code >= 400:
                    raise RuntimeError("HTTP " + str(resp.status_code))
                
                with open(PHISHTANK_LOCAL_DB, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                
                line_count = resp.text.count("\n")
                app.logger.info("[PhishGuard] PhishTank dataset refreshed: %d lines", line_count)
                # Clear the cache so it reloads next time
                with _CACHE_LOCK:
                    if "phishtank_local_feed::" + PHISHTANK_LOCAL_DB in _CACHE:
                        del _CACHE["phishtank_local_feed::" + PHISHTANK_LOCAL_DB]
            except Exception as ex:
                app.logger.warning("[PhishGuard] PhishTank dataset refresh failed: %s", str(ex))
        
        app.logger.info("[PhishGuard] Feed refresh cycle completed")
    except Exception as ex:
        app.logger.error("[PhishGuard] Feed refresh cycle failed: %s", str(ex))


def _feed_refresh_worker():
    """Background worker thread for refreshing feeds every hour"""
    global _BACKGROUND_THREAD_ACTIVE
    app.logger.info("[PhishGuard] Feed refresh worker thread started")
    while _BACKGROUND_THREAD_ACTIVE:
        try:
            time.sleep(60 * 60)  # Wait 1 hour
            if _BACKGROUND_THREAD_ACTIVE:
                refresh_feeds()
        except Exception as ex:
            app.logger.error("[PhishGuard] Feed worker error: %s", str(ex))
    app.logger.info("[PhishGuard] Feed refresh worker thread stopped")


def start_background_feeds():
    """Start background thread for feed updates"""
    global _BACKGROUND_THREAD, _BACKGROUND_THREAD_ACTIVE
    if _BACKGROUND_THREAD_ACTIVE:
        return
    
    _BACKGROUND_THREAD_ACTIVE = True
    _BACKGROUND_THREAD = threading.Thread(target=_feed_refresh_worker, daemon=True)
    _BACKGROUND_THREAD.start()
    app.logger.info("[PhishGuard] Background feed refresh thread started")

# ---------------------------------------------------------------------------
#  Trusted Apex Domains (whitelist)
# ---------------------------------------------------------------------------
TRUSTED_APEX = {
    "google.com", "youtube.com", "gmail.com", "google.co.uk", "google.ca",
    "accounts.google.com", "mail.google.com",
    "facebook.com", "instagram.com", "whatsapp.com", "messenger.com",
    "twitter.com", "x.com", "t.co",
    "microsoft.com", "office.com", "microsoft365.com", "live.com",
    "outlook.com", "hotmail.com", "windows.com", "azure.com", "bing.com",
    "login.microsoftonline.com", "microsoftonline.com",
    "apple.com", "icloud.com", "itunes.com",
    "amazon.com", "amazon.co.uk", "amazon.de", "aws.com", "amazonaws.com",
    "flipkart.com", "myntra.com",
    "github.com", "gitlab.com", "stackoverflow.com",
    "wikipedia.org", "wikimedia.org",
    "linkedin.com", "reddit.com",
    "netflix.com", "spotify.com", "twitch.tv", "tiktok.com", "discord.com",
    "zoom.us", "slack.com", "dropbox.com", "box.com",
    "paypal.com", "ebay.com", "etsy.com", "shopify.com",
    "yahoo.com", "ymail.com",
    "cloudflare.com", "cloudflare.net",
    "adobe.com", "notion.so",
    "openai.com", "chat.openai.com",
    "nytimes.com", "bbc.com", "cnn.com", "theguardian.com",
    "bankofamerica.com", "chase.com", "wellsfargo.com", "citibank.com",
    "signin.ebay.com",
}


def is_trusted_domain(domain):
    d = (domain or "").lower().strip(".")
    for apex in TRUSTED_APEX:
        if d == apex or d.endswith("." + apex):
            return True
    return False


# ---------------------------------------------------------------------------
#  URL Normalization and Validation
# ---------------------------------------------------------------------------
_URL_RE = re.compile(
    r'^https?://'
    r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)*'
    r'(?:[A-Z]{2,63}|XN--[A-Z0-9]{1,59})'
    r'(?::\d{2,5})?'
    r'(?:/[^\s]*)?$',
    re.IGNORECASE
)

_IP_URL_RE = re.compile(
    r'^https?://\d{1,3}(\.\d{1,3}){3}(:\d{2,5})?(/.*)?$',
    re.IGNORECASE
)


def normalize_url(raw):
    url = raw.strip()
    if not url:
        return ""
    if not re.match(r'^https?://', url, re.I):
        url = "https://" + url
    url = unquote(url)
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    port_part = ""
    if parsed.port and parsed.port not in (80, 443):
        port_part = ":" + str(parsed.port)
    rest = parsed.path
    if parsed.query:
        rest += "?" + parsed.query
    if parsed.fragment:
        rest += "#" + parsed.fragment
    url = scheme + "://" + host + port_part + rest
    return url


def validate_url(url):
    if not url:
        return "Empty URL provided"
    if len(url) > 2048:
        return "URL exceeds maximum length (2048 chars)"
    if _URL_RE.match(url) or _IP_URL_RE.match(url):
        return None
    if "@" in url:
        return None
    return "Invalid URL format"


# ---------------------------------------------------------------------------
#  Typosquatting / Brand-Impersonation Engine
# ---------------------------------------------------------------------------
KNOWN_BRANDS = [
    "google", "youtube", "facebook", "instagram", "twitter", "microsoft",
    "apple", "amazon", "github", "paypal", "ebay", "yahoo", "netflix",
    "spotify", "linkedin", "reddit", "dropbox", "adobe", "outlook", "gmail",
    "discord", "twitch", "tiktok", "slack", "notion", "shopify", "etsy",
    "bankofamerica", "wellsfargo", "chase", "citibank", "hsbc", "barclays",
    "amex", "visa", "mastercard",
]


def _leet_normalize(s):
    table = {
        "0": "o", "1": "l", "3": "e", "4": "a", "5": "s",
        "6": "g", "7": "t", "8": "b", "@": "a", "!": "i",
    }
    return "".join(table.get(c, c) for c in s.lower())


def _levenshtein(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for ch in a:
        curr = [prev[0] + 1]
        for j, dh in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[-1] + 1, prev[j] + (ch != dh)))
        prev = curr
    return prev[-1]


def check_brand_impersonation(domain):
    domain = (domain or "").lower()
    
    # Skip checking if it's a trusted domain
    if is_trusted_domain(domain):
        return None
    
    # CRITICAL: Check if any brand keyword appears directly in the domain
    # This catches impersonation like "amazon-security-alert.xyz"
    for brand in KNOWN_BRANDS:
        if brand in domain.split(".")[0]:  # Check in the main domain part
            # Make sure it's not just a coincidence (brand name should be significant)
            main_part = domain.split(".")[0]
            if main_part.startswith(brand) or main_part.endswith(brand):
                return brand
    
    parts = domain.split(".")
    candidates = set()
    if len(parts) >= 2:
        sld = parts[-2]
        candidates.add(sld)
        candidates.add(sld.replace("-", ""))
        if "-" in sld:
            candidates.add(sld.split("-")[0])
    for candidate in candidates:
        norm = _leet_normalize(candidate)
        for brand in KNOWN_BRANDS:
            if candidate == brand:
                continue
            if norm == brand:
                return brand
            if abs(len(norm) - len(brand)) <= 3:
                dist = _levenshtein(norm, brand)
                if len(brand) >= 5 and dist <= 1:
                    return brand
                if len(brand) >= 6 and dist <= 2:
                    return brand
    return None


def check_domain_spoofing(domain):
    flags = []
    d = (domain or "").lower()
    parts = d.split(".")
    
    # Check for suspicious platform domains used for phishing
    suspicious_platforms = [".appspot.com", ".github.io", ".blogspot.com", ".herokuapp.com", ".netlify.app"]
    for platform in suspicious_platforms:
        if d.endswith(platform) and not is_trusted_domain(d):
            flags.append(f"Suspicious hosting platform '{platform}' -- common in phishing attacks")
    
    if len(parts) >= 3:
        full = ".".join(parts)
        for apex in TRUSTED_APEX:
            if full.startswith(apex + ".") and not is_trusted_domain(d):
                flags.append("Domain spoofing: '" + apex + "' used as subdomain of untrusted domain")
            brand_part = apex.split(".")[0]
            for part in parts[:-2]:
                if brand_part in part and not is_trusted_domain(d):
                    if part != brand_part:
                        flags.append("Brand name '" + brand_part + "' embedded in subdomain '" + part + "'")
                        break
    return flags


# ---------------------------------------------------------------------------
#  Feature Extraction (must match training columns)
# ---------------------------------------------------------------------------
def extract_features(url):
    parsed = urlparse(url)
    domain = parsed.hostname or ""
    return {
        "URLLength":     len(url),
        "DomainLength":  len(domain),
        "IsDomainIP":    1 if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain) else 0,
        "TLDLength":     len(domain.split(".")[-1]) if "." in domain else 0,
        "NoOfSubDomain": max(domain.count(".") - 1, 0),
        "IsHTTPS":       1 if parsed.scheme == "https" else 0,
    }

# ---------------------------------------------------------------------------
#  Heuristic Rule Engine  16+ Rules
# ---------------------------------------------------------------------------
SUSPICIOUS_KEYWORDS = [
    "login", "verify", "secure", "bank", "account", "update", "confirm",
    "password", "credential", "signin", "paypal", "ebay", "amazon",
    "billing", "support", "alert", "suspended", "limited", "unusual",
    "auth", "wallet", "recover", "reset", "webscr", "cmd=_", "checkout",
    "malware", "phishing", "testing", "exploit", "backdoor", "trojan",
    "virus", "ransomware", "scam", "fraud", "steal", "hack",
]

SUSPICIOUS_TLDS = {
    ".xyz", ".tk", ".ml", ".ga", ".cf", ".gq",
    ".pw", ".top", ".zip", ".click", ".country", ".buzz", ".work", ".surf",
    ".test", ".local", ".localhost", ".invalid", ".example", ".mock",
}

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly",
    "is.gd", "buff.ly", "short.link", "rebrand.ly", "cutt.ly",
}

INTEL_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "is.gd", "goo.gl", "ow.ly"}
IMPERSONATION_TRUSTED = {"paypal", "google", "amazon", "facebook", "microsoft", "apple"}


def check_ssl_certificate_age(url):
    """
    Check the age of SSL certificate for a domain.
    Returns certificate age in days and associated risk.
    
    Risk scoring:
    - < 2 days: 50 risk (highly suspicious)
    - < 7 days: 25 risk (suspicious)
    - < 30 days: 10 risk (somewhat suspicious)
    - >= 30 days: 0 risk (normal)
    """
    parsed = urlparse(url)
    domain = (parsed.hostname or "").lower()
    
    result = {
        "status": "unavailable",
        "domain": domain,
        "certificate_age_days": None,
        "risk": 0,
        "details": "SSL certificate check unavailable",
    }

    # Skip IP addresses - they don't have SSL certs with domain names
    if not domain or re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
        result["details"] = "IP-based host; SSL check skipped"
        return result

    # Skip non-HTTPS URLs
    if parsed.scheme and parsed.scheme.lower() != "https":
        result["details"] = "Non-HTTPS URL; SSL check skipped"
        return result

    cache_key = "ssl_cert::" + domain
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        app.logger.info("[PhishGuard] SSL certificate check: %s", domain)
        
        # Create SSL context with certificate verification disabled
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Connect to domain on port 443
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                # Get certificate
                der_cert = ssock.getpeercert(binary_form=True)
                
                if not der_cert:
                    result["status"] = "unavailable"
                    result["details"] = "No SSL certificate found"
                    _cache_set(cache_key, result, 2 * 3600)
                    return result
                
                # Parse certificate with OpenSSL
                x509 = crypto.load_certificate(crypto.FILETYPE_ASN1, der_cert)
                
                # Extract notBefore date
                not_before_str = x509.get_notBefore().decode('utf-8')
                # Format: YYYYMMDDhhmmssZ (example: 20240315120000Z)
                cert_issue_date = datetime.datetime.strptime(not_before_str, "%Y%m%d%H%M%SZ")
                
                # Calculate certificate age
                now = datetime.datetime.utcnow()
                cert_age_days = max((now - cert_issue_date).days, 0)
                
                result["status"] = "ok"
                result["certificate_age_days"] = cert_age_days
                
                # Assign risk based on certificate age
                if cert_age_days < 2:
                    result["risk"] = 50
                    result["details"] = f"SSL certificate issued {cert_age_days} days ago (highly suspicious - very new)"
                elif cert_age_days < 7:
                    result["risk"] = 25
                    result["details"] = f"SSL certificate issued {cert_age_days} days ago (suspicious - recently issued)"
                elif cert_age_days < 30:
                    result["risk"] = 10
                    result["details"] = f"SSL certificate issued {cert_age_days} days ago (somewhat suspicious - new)"
                else:
                    result["risk"] = 0
                    result["details"] = f"SSL certificate issued {cert_age_days} days ago (normal age)"
                
                app.logger.info(
                    "[PhishGuard] SSL certificate age for %s: %d days, risk: %d",
                    domain, cert_age_days, result["risk"]
                )
                
                # Cache for 24 hours
                _cache_set(cache_key, result, 24 * 3600)
                return result
    
    except socket.timeout:
        app.logger.warning("[PhishGuard] SSL check timeout for %s", domain)
        result["status"] = "unavailable"
        result["details"] = "SSL check timed out"
        result["risk"] = 0
        _cache_set(cache_key, result, 1 * 3600)
        return result
    
    except socket.gaierror:
        app.logger.warning("[PhishGuard] Domain resolution failed for %s", domain)
        result["status"] = "unavailable"
        result["details"] = "Domain could not be resolved"
        result["risk"] = 0
        _cache_set(cache_key, result, 1 * 3600)
        return result
    
    except ssl.SSLError as ex:
        app.logger.warning("[PhishGuard] SSL error for %s: %s", domain, str(ex))
        result["status"] = "unavailable"
        result["details"] = "SSL error occurred"
        result["risk"] = 0
        _cache_set(cache_key, result, 1 * 3600)
        return result
    
    except Exception as ex:
        app.logger.warning("[PhishGuard] SSL certificate check failed for %s: %s", domain, str(ex))
        result["status"] = "unavailable"
        result["details"] = "SSL certificate check unavailable"
        result["risk"] = 0
        _cache_set(cache_key, result, 30 * 60)
        return result


def check_google_safe_browsing(url):
    result = {
        "status": "ok",
        "flagged": False,
        "risk": 0,
        "details": "No threats detected",
    }
    
    if not GOOGLE_SAFE_BROWSING_API_KEY:
        result["status"] = "unavailable"
        result["details"] = "API key not configured"
        return result

    cache_key = "google_sb::" + url
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    endpoint = (
        "https://safebrowsing.googleapis.com/v4/threatMatches:find?key="
        + GOOGLE_SAFE_BROWSING_API_KEY
    )
    payload = {
        "client": {"clientId": "phishguard-ai", "clientVersion": "3.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    try:
        app.logger.info("[PhishGuard] Google Safe Browsing check: %s", url)
        resp = requests.post(endpoint, json=payload, timeout=8)
        
        # Handle 403 - API key issue or rate limit
        if resp.status_code == 403:
            app.logger.error("[PhishGuard] Google Safe Browsing 403 - API key or rate limit issue")
            result["status"] = "error"
            result["details"] = "API authentication error (403) - check not available"
            # API is broken, don't penalize - just mark as unavailable
            result["risk"] = 0  # Don't add risk when API is broken
            result["flagged"] = False
            _cache_set(cache_key, result, 5 * 60)
            return result
        
        if resp.status_code >= 400:
            raise RuntimeError("HTTP " + str(resp.status_code))
        
        data = resp.json() if resp.content else {}
        matches = data.get("matches", [])
        if matches:
            result["flagged"] = True
            result["risk"] = 60
            result["details"] = "Flagged: " + ", ".join([m.get("threatType", "unknown") for m in matches[:3]])
        app.logger.info("[PhishGuard] Google Safe Browsing result: flagged=%s", result["flagged"])
        _cache_set(cache_key, result, 30 * 60)
        return result
    except Exception as ex:
        app.logger.warning("[PhishGuard] Google Safe Browsing failed for %s: %s", url, str(ex))
        result["status"] = "error"
        result["details"] = "Check unavailable"
        _cache_set(cache_key, result, 5 * 60)
        return result


def check_phishtank(url):
    result = {
        "status": "ok",
        "found": False,
        "risk": 0,
        "details": "Not found in PhishTank",
    }

    cache_key = "phishtank::" + url
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        # Try local CSV first (either from env var or auto-downloaded)
        local_db_path = PHISHTANK_LOCAL_DB if PHISHTANK_LOCAL_DB else None
        
        if local_db_path and os.path.exists(local_db_path):
            app.logger.info("[PhishGuard] PhishTank check (local): %s", url)
            feed_key = "phishtank_local_feed::" + local_db_path
            local_urls = _cache_get(feed_key)
            if local_urls is None:
                try:
                    with open(local_db_path, "r", encoding="utf-8", errors="ignore") as fh:
                        reader = csv.DictReader(fh)
                        local_urls = set()
                        for row in reader:
                            if row and "url" in row:
                                local_urls.add(row["url"].strip())
                    _cache_set(feed_key, local_urls, 20 * 60)
                    app.logger.info("[PhishGuard] Loaded %d URLs from PhishTank CSV", len(local_urls))
                except Exception as e:
                    app.logger.warning("[PhishGuard] Failed to load local PhishTank CSV: %s", str(e))
                    local_urls = set()
            
            if url in local_urls:
                result["found"] = True
                result["risk"] = 70
                result["details"] = "Found in PhishTank dataset"
            _cache_set(cache_key, result, 20 * 60)
            return result

        # Try API if key is provided
        if PHISHTANK_API_KEY:
            app.logger.info("[PhishGuard] PhishTank check (API): %s", url)
            payload = {"url": url, "format": "json", "app_key": PHISHTANK_API_KEY}
            resp = requests.post("https://checkurl.phishtank.com/checkurl/", data=payload, timeout=8)
            if resp.status_code >= 400:
                raise RuntimeError("HTTP " + str(resp.status_code))
            data = resp.json()
            results = data.get("results", {})
            if bool(results.get("in_database")) and bool(results.get("valid")):
                result["found"] = True
                result["risk"] = 70
                result["details"] = "Found in PhishTank"
            _cache_set(cache_key, result, 30 * 60)
            return result
        
        # No API key and no local DB - return unavailable
        if not local_urls:
            app.logger.info("[PhishGuard] PhishTank check unavailable (no API key, no local DB)")
            result["status"] = "ok"
            result["details"] = "PhishTank dataset not available"
        
        _cache_set(cache_key, result, 5 * 60)
        return result
    except Exception as ex:
        app.logger.warning("[PhishGuard] PhishTank check failed for %s: %s", url, str(ex))
        result["status"] = "ok"
        result["details"] = "Check unavailable"
        _cache_set(cache_key, result, 5 * 60)
        return result


def detect_domain_impersonation(domain):
    d = (domain or "").lower().strip(".")
    result = {
        "status": "ok",
        "is_similar": False,
        "risk": 0,
        "details": "No brand impersonation detected",
        "matched_brand": None,
        "similarity": 0.0,
    }
    if not d:
        result["status"] = "error"
        result["details"] = "No domain provided"
        return result

    # Skip checking if it's a trusted domain
    if is_trusted_domain(d):
        result["details"] = "Trusted domain - brand check skipped"
        return result

    parts = d.split(".")
    candidate = parts[-2] if len(parts) >= 2 else d
    norm = _leet_normalize(candidate.replace("-", ""))

    best_brand = None
    best_similarity = 0.0
    for brand in IMPERSONATION_TRUSTED:
        if norm == brand:
            continue
        max_len = max(len(norm), len(brand))
        if max_len == 0:
            continue
        dist = _levenshtein(norm, brand)
        similarity = 1.0 - (float(dist) / float(max_len))
        if similarity > best_similarity:
            best_similarity = similarity
            best_brand = brand

    result["matched_brand"] = best_brand
    result["similarity"] = round(best_similarity, 3)
    if best_brand and best_similarity >= 0.88:
        result["is_similar"] = True
        result["risk"] = 30
        result["details"] = "Domain resembles trusted brand '" + best_brand + "'"
    elif best_brand and best_similarity >= 0.80:
        result["is_similar"] = True
        result["risk"] = 18
        result["details"] = "Domain moderately resembles trusted brand '" + best_brand + "'"

    return result


def check_redirect_chain(url):
    result = {
        "status": "ok",
        "redirect_count": 0,
        "final_url": url,
        "risk": 0,
        "details": "No suspicious redirects",
    }
    cache_key = "redirects::" + url
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        app.logger.info("[PhishGuard] Redirect detection: %s", url)
        resp = requests.get(url, allow_redirects=True, timeout=10, verify=False)
        redirect_count = len(resp.history)
        result["redirect_count"] = redirect_count
        result["final_url"] = resp.url
        
        if redirect_count > 5:
            result["risk"] = 30
            result["details"] = "High-risk redirect chain (" + str(redirect_count) + " redirects)"
        elif redirect_count > 3:
            result["risk"] = 15
            result["details"] = "Suspicious redirect chain (" + str(redirect_count) + " redirects)"
        else:
            result["details"] = "Normal redirect count (" + str(redirect_count) + ")"
        
        app.logger.info("[PhishGuard] Redirect result: count=%d, risk=%d", redirect_count, result["risk"])
        _cache_set(cache_key, result, 10 * 60)
        return result
    except requests.exceptions.Timeout:
        app.logger.warning("[PhishGuard] Redirect check timeout for %s", url)
        result["status"] = "ok"
        result["details"] = "Redirect check timed out"
        _cache_set(cache_key, result, 5 * 60)
        return result
    except Exception as ex:
        app.logger.warning("[PhishGuard] Redirect check failed for %s: %s", url, str(ex))
        result["status"] = "ok"
        result["details"] = "Could not check redirects"
        _cache_set(cache_key, result, 5 * 60)
        return result


def check_shortened_url(url):
    parsed = urlparse(url)
    domain = (parsed.hostname or "").lower()
    result = {
        "status": "ok",
        "is_shortened": False,
        "shortener": None,
        "expanded_url": url,
        "risk": 0,
        "details": "Not a known URL shortener",
    }

    matched = None
    for shortener in INTEL_SHORTENERS:
        if domain == shortener or domain.endswith("." + shortener):
            matched = shortener
            break

    if not matched:
        return result

    result["is_shortened"] = True
    result["shortener"] = matched
    result["risk"] = 10
    result["details"] = "Shortened URL detected"

    cache_key = "short_url_expand::" + url
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.head(url, allow_redirects=True, timeout=8)
        expanded = resp.url or url
        result["expanded_url"] = expanded
        _cache_set(cache_key, result, 30 * 60)
        return result
    except Exception:
        try:
            resp = requests.get(url, allow_redirects=True, timeout=8)
            result["expanded_url"] = resp.url or url
            _cache_set(cache_key, result, 30 * 60)
            return result
        except Exception as ex:
            app.logger.warning("Short URL expansion failed for %s: %s", url, ex)
            result["status"] = "error"
            result["details"] = "Could not expand shortened URL"
            _cache_set(cache_key, result, 5 * 60)
            return result


def check_openphish_feed(url):
    result = {
        "status": "ok",
        "found": False,
        "risk": 0,
        "details": "Not found in OpenPhish feed",
    }
    cache_key = "openphish::" + url
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    feed_key = "openphish_feed"
    feed = _cache_get(feed_key)
    if feed is None:
        try:
            app.logger.info("[PhishGuard] Downloading OpenPhish feed...")
            resp = requests.get("https://openphish.com/feed.txt", timeout=10)
            if resp.status_code >= 400:
                raise RuntimeError("HTTP " + str(resp.status_code))
            feed = {line.strip() for line in resp.text.splitlines() if line.strip()}
            app.logger.info("[PhishGuard] OpenPhish feed loaded: %d URLs", len(feed))
            _cache_set(feed_key, feed, 60 * 60)
        except Exception as ex:
            app.logger.warning("[PhishGuard] OpenPhish feed download failed: %s", str(ex))
            result["status"] = "unavailable"
            result["details"] = "Feed unavailable"
            _cache_set(cache_key, result, 5 * 60)
            return result

    app.logger.info("[PhishGuard] OpenPhish check: %s", url)
    if url in feed:
        result["found"] = True
        result["risk"] = 75
        result["details"] = "Found in OpenPhish feed"
    
    _cache_set(cache_key, result, 60 * 60)
    return result





def run_heuristics(url):
    flags = []
    score = 0
    url_lower = url.lower()
    parsed = urlparse(url_lower)
    domain = parsed.hostname or ""
    path = parsed.path or ""

    # Rule 1: IP address as hostname
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
        flags.append("IP address used instead of domain name")
        score += 40

    # Rule 2: HTTP (no SSL)
    if parsed.scheme == "http":
        flags.append("Unsecured HTTP connection (no SSL/TLS)")
        score += 10

    # Rule 3: Suspicious TLD
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            flags.append("Suspicious top-level domain: " + tld)
            score += 20
            break

    # Rule 4: Known URL shortener (exact domain matching, not substring)
    for shortener in URL_SHORTENERS:
        if domain == shortener or domain.endswith("." + shortener):
            flags.append("URL shortener detected (" + shortener + ") -- real destination hidden")
            score += 15
            break

    # Rule 5: Suspicious keywords (skip for trusted domains)
    if not is_trusted_domain(domain):
        found = [k for k in SUSPICIOUS_KEYWORDS if k in url_lower]
        if found:
            flags.append("Suspicious keywords: " + ", ".join(found[:5]))
            score += min(len(found) * 8, 25)

    # Rule 6: Excessive hyphens in domain
    if domain.count("-") >= 3:
        flags.append("Excessive hyphens in domain (" + str(domain.count("-")) + " found)")
        score += 15

    # Rule 7: URL length
    if len(url) > 100:
        flags.append("Unusually long URL (" + str(len(url)) + " chars)")
        score += 10
    elif len(url) > 75:
        flags.append("Long URL (" + str(len(url)) + " chars)")
        score += 5

    # Rule 8: Too many subdomains
    sub_count = max(domain.count(".") - 1, 0)
    if sub_count >= 3:
        flags.append("Too many subdomains (" + str(sub_count) + ") -- common in phishing")
        score += 15

    # Rule 9: @ symbol redirect trick
    if "@" in url:
        flags.append("'@' symbol in URL -- browser ignores everything before it")
        score += 25

    # Rule 10: Double-slash in path
    if "//" in path:
        flags.append("Double slash in path -- possible open redirect trick")
        score += 10

    # Rule 11: Non-standard port
    if parsed.port and parsed.port not in (80, 443):
        flags.append("Non-standard port number: " + str(parsed.port))
        score += 15

    # Rule 12: Punycode / IDN homograph
    if "xn--" in domain:
        flags.append("Punycode/IDN domain (possible lookalike homograph attack)")
        score += 20

    # Rule 13: Excessive dots (> 4)
    if domain.count(".") > 4:
        flags.append("Excessive dots in domain (" + str(domain.count(".")) + " found)")
        score += 10

    # Rule 14: Hex-encoded characters
    if re.search(r"%[0-9a-f]{2}", url_lower):
        flags.append("Hex-encoded characters in URL -- possible obfuscation")
        score += 10

    # Rule 14.5: CRITICAL - Explicit phishing/malware/exploit keywords in domain or path
    critical_keywords = ["malware", "phishing", "exploit", "backdoor", "trojan", "ransomware", "scam", "fraud"]
    found_critical = [kw for kw in critical_keywords if kw in url_lower]
    if found_critical:
        flags.append("CRITICAL: Malicious keywords detected -- " + ", ".join(found_critical))
        score += 80  # Massive score increase for explicit malicious indicators

    # Rule 15: Typosquatting / brand impersonation (Levenshtein)
    impersonated = check_brand_impersonation(domain)
    if impersonated:
        flags.append("Brand impersonation detected -- mimics '" + impersonated + "' (typosquatting/leet-speak)")
        score += 45

    # Rule 16: Domain spoofing patterns
    spoof_flags = check_domain_spoofing(domain)
    for sf in spoof_flags:
        flags.append(sf)
        score += 20

    return flags, min(score, 100)


# ---------------------------------------------------------------------------
#  Risk Level Classification
# ---------------------------------------------------------------------------
def get_risk_level(combined, is_phishing):
    if not is_phishing:
        if combined < 0.15:
            return "safe"
        return "low"
    if combined >= 0.75:
        return "critical"
    if combined >= 0.55:
        return "high"
    return "medium"


def _legacy_decision_logic(url, ml_score, heuristic_score):
    parsed_domain = urlparse(url).hostname or ""
    trusted = is_trusted_domain(parsed_domain)

    rule_probability = heuristic_score / 100.0
    combined_score = (0.6 * ml_score) + (0.4 * rule_probability)

    # TRUST OVERRIDE: If domain is in whitelist and no heuristic flags, trust it
    if trusted:
        if heuristic_score == 0:
            # Trusted domain with no heuristic red flags = safe
            is_phishing = False
            combined_score = ml_score * 0.10  # heavily discount ML score for trusted domains
        else:
            # Trusted domain but has heuristic flags (shouldn't happen often)
            is_phishing = False
            combined_score = min(combined_score, 0.40)
    elif heuristic_score >= 40:
        is_phishing = True
        combined_score = max(combined_score, 0.50)
    elif ml_score >= 0.50:
        is_phishing = True
    elif combined_score >= 0.35:
        is_phishing = True
    else:
        is_phishing = False
    return is_phishing, combined_score


def analyze_url(url):
    features = extract_features(url)
    df = pd.DataFrame([features])
    try:
        proba = model.predict_proba(df)[0]
        ml_score = float(proba[1])
    except Exception as ex:
        app.logger.warning("Model inference failed for %s: %s", url, ex)
        ml_score = 0.5

    flags, heuristic_score = run_heuristics(url)
    parsed_domain = urlparse(url).hostname or ""

    checks = {
        "ssl_certificate_age": check_ssl_certificate_age(url),
        "google_safe_browsing": check_google_safe_browsing(url),
        "phishtank": check_phishtank(url),
        "domain_similarity": detect_domain_impersonation(parsed_domain),
        "redirects": check_redirect_chain(url),
        "shortened_url": check_shortened_url(url),
        "openphish": check_openphish_feed(url),
    }

    intel_risk = 0
    intel_flags = []
    for name, details in checks.items():
        risk_delta = int(details.get("risk", 0) or 0)
        intel_risk += risk_delta
        if risk_delta > 0:
            intel_flags.append(name + ": " + str(details.get("details", "flagged")))

    intel_risk = min(intel_risk, 100)
    normalized_intel = float(intel_risk) / 100.0
    base_combined = (0.50 * ml_score) + (0.30 * (heuristic_score / 100.0)) + (0.20 * normalized_intel)

    confirmed_threat = any([
        checks["google_safe_browsing"].get("flagged"),
        checks["phishtank"].get("found"),
        checks["openphish"].get("found"),
    ])

    legacy_is_phishing, legacy_combined = _legacy_decision_logic(url, ml_score, heuristic_score)
    is_phishing = legacy_is_phishing or confirmed_threat or base_combined >= 0.60
    if confirmed_threat:
        base_combined = max(base_combined, 0.85)

    risk_score = int(round(min(max(base_combined * 100.0, legacy_combined * 100.0), 100.0)))
    
    legacy_risk_level = get_risk_level(float(risk_score) / 100.0, is_phishing)
    all_flags = flags + intel_flags
    
    # Trust override: For trusted domains with no heuristic flags, treat as safe regardless of ML score
    parsed_domain = urlparse(url).hostname or ""
    if is_trusted_domain(parsed_domain) and heuristic_score == 0:
        is_phishing = False
        normalized_level = "SAFE"
        risk_score = int(round(min(max(base_combined * 100.0, legacy_combined * 100.0) * 0.10, 20)))
    elif is_phishing:
        normalized_level = "PHISHING"
    elif risk_score >= 35:
        normalized_level = "SUSPICIOUS"
    else:
        normalized_level = "SAFE"
    
    # CRITICAL CHECK: If any flag contains explicit malicious keywords, force PHISHING
    has_critical_flag = any("CRITICAL" in flag or "malicious" in flag.lower() for flag in all_flags)
    if has_critical_flag:
        is_phishing = True
        normalized_level = "PHISHING"
        risk_score = max(risk_score, 75)  # Ensure high risk score
    
    # CHECK: If heuristic score >= 40 or multiple serious flags, force PHISHING
    num_serious_flags = sum(1 for flag in all_flags if any(kw in flag.lower() for kw in ["critical", "ip address", "@ symbol", "malware", "phishing", "exploit"]))
    if num_serious_flags >= 2 or heuristic_score >= 40:
        is_phishing = True
        normalized_level = "PHISHING"
        risk_score = max(risk_score, 65)

    return {
        "url": url,
        "ml_prediction": "phishing" if ml_score >= 0.50 else "legitimate",
        "risk_score": risk_score,
        "risk_level": normalized_level,
        "checks": checks,
        "result": "phishing" if is_phishing else "legitimate",
        "confidence": round(float(risk_score), 1),
        "ml_score": round(ml_score * 100, 1),
        "rule_score": heuristic_score,
        "combined_score": round(float(risk_score), 1),
        "risk_level_legacy": legacy_risk_level,
        "flags": all_flags,
    }


# ---------------------------------------------------------------------------
#  /predict  endpoint
# ---------------------------------------------------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    raw_url = data.get("url", "").strip()

    if not raw_url:
        return jsonify({"error": "No URL provided"}), 400

    url = normalize_url(raw_url)
    error = validate_url(url)
    if error:
        return jsonify({"error": error}), 400

    analysis = analyze_url(url)

    # Keep backward-compatible fields while exposing new structured intelligence output.
    return jsonify({
        "url": analysis["url"],
        "ml_prediction": analysis["ml_prediction"],
        "risk_score": analysis["risk_score"],
        "risk_level": analysis["risk_level"],
        "risk_level_legacy": analysis["risk_level_legacy"],
        "checks": analysis["checks"],
        "result": analysis["result"],
        "confidence": analysis["confidence"],
        "ml_score": analysis["ml_score"],
        "rule_score": analysis["rule_score"],
        "combined_score": analysis["combined_score"],
        "flags": analysis["flags"],
    })


# ---------------------------------------------------------------------------
#  /chat  endpoint  (Explainable AI)
# ---------------------------------------------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    result = data.get("result", "unknown")
    confidence = data.get("confidence", 0)
    flags = data.get("flags", [])
    url = data.get("url", "")
    risk_level = data.get("risk_level", "unknown")
    ml_score = data.get("ml_score", 0)
    rule_score = data.get("rule_score", 0)

    parsed = urlparse(url)
    domain = parsed.hostname or url

    if result == "phishing":
        risk_emoji = "??" if risk_level in ("critical", "high") else "??"
        intro = (
            risk_emoji + " **Threat Analysis -- PHISHING DETECTED**\n\n"
            "**Target URL:** `" + str(url) + "`\n"
            "**Domain:** `" + str(domain) + "`\n"
            "**Risk Level:** " + str(risk_level).upper() + "\n"
            "**Confidence:** " + str(confidence) + "%\n"
            "**ML Score:** " + str(ml_score) + "% | **Rule Score:** " + str(rule_score) + "/100\n"
        )

        if flags:
            flag_text = "\n".join("  * " + f for f in flags)
            detail = "\n**Triggered Indicators (" + str(len(flags)) + "):**\n" + flag_text + "\n"
        else:
            detail = (
                "\n**Analysis:**\n"
                "  * The machine learning model detected statistical patterns "
                "strongly associated with phishing pages.\n"
            )

        risk_explanation = "\n**Risk Explanation:**\n"
        has_explanation = False
        for f in flags:
            fl = f.lower()
            if "brand impersonation" in fl or "typosquat" in fl:
                risk_explanation += (
                    "  * This domain closely mimics a well-known brand (typosquatting). "
                    "Attackers register lookalike domains to trick users into entering credentials.\n"
                )
                has_explanation = True
                break
        for f in flags:
            if "ip address" in f.lower():
                risk_explanation += (
                    "  * Legitimate services use domain names, not raw IP addresses. "
                    "IP-based URLs are frequently used in phishing kits.\n"
                )
                has_explanation = True
                break
        for f in flags:
            if "@" in f:
                risk_explanation += (
                    "  * The '@' symbol causes the browser to ignore everything before it, "
                    "making the URL appear to belong to a trusted domain.\n"
                )
                has_explanation = True
                break
        for f in flags:
            fl = f.lower()
            if "subdomain" in fl or "spoof" in fl:
                risk_explanation += (
                    "  * Multiple subdomains or embedded brand names are used to make "
                    "the URL look legitimate at first glance.\n"
                )
                has_explanation = True
                break
        if not has_explanation:
            risk_explanation += (
                "  * Multiple signals combine to indicate this URL is designed "
                "to deceive users into revealing sensitive information.\n"
            )

        advice = (
            "\n**Security Recommendation:**\n"
            "  * Do **NOT** visit this URL or enter any personal information.\n"
            "  * If received via email or message, report it as phishing.\n"
            "  * Delete the message and block the sender.\n"
            "  * If you already entered credentials, change your passwords immediately "
            "and enable two-factor authentication."
        )

    else:
        intro = (
            "**Threat Analysis -- NO THREATS DETECTED**\n\n"
            "**Target URL:** `" + str(url) + "`\n"
            "**Domain:** `" + str(domain) + "`\n"
            "**Risk Level:** " + str(risk_level).upper() + "\n"
            "**Confidence:** " + str(round(100 - confidence, 1)) + "% safe\n"
            "**ML Score:** " + str(ml_score) + "% | **Rule Score:** " + str(rule_score) + "/100\n"
        )

        if flags:
            flag_text = "\n".join("  * " + f for f in flags)
            detail = (
                "\n**Minor Observations (" + str(len(flags)) + "):**\n" + flag_text + "\n"
                "\nThese indicators alone are not sufficient to classify the URL as phishing, "
                "but warrant caution.\n"
            )
        else:
            detail = (
                "\n**Analysis:**\n"
                "  * No suspicious patterns were detected for `" + str(domain) + "`.\n"
                "  * Both the ML model and heuristic engine returned low-risk scores.\n"
            )

        risk_explanation = ""
        advice = (
            "\n**Security Reminder:**\n"
            "  * Always verify the domain carefully before entering sensitive information.\n"
            "  * Look for the padlock icon indicating HTTPS encryption.\n"
            "  * Be cautious of unsolicited links, even from known contacts.\n"
            "  * Keep your browser and security software up to date."
        )

    return jsonify({"explanation": intro + detail + risk_explanation + advice})


# ---------------------------------------------------------------------------
#  /whois  endpoint  Domain Intelligence
# ---------------------------------------------------------------------------
@app.route("/whois", methods=["POST"])
def whois_lookup():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    url = normalize_url(url)
    parsed = urlparse(url)
    domain = parsed.hostname or ""

    info = {
        "domain": domain,
        "scheme": parsed.scheme,
        "port": parsed.port,
        "ip_addresses": [],
        "is_trusted": is_trusted_domain(domain),
        "lookup_time": datetime.datetime.utcnow().isoformat() + "Z",
    }

    try:
        addrs = socket.getaddrinfo(domain, None)
        ips = list(set(addr[4][0] for addr in addrs))
        info["ip_addresses"] = ips[:5]
    except socket.gaierror:
        info["ip_addresses"] = []
        info["dns_error"] = "Domain could not be resolved"

    return jsonify(info)


# ---------------------------------------------------------------------------
#  /health
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model": MODEL_PATH,
        "version": "3.0.0",
        "engine": "ML + Heuristic + Threat Intel Hybrid",
    })


if __name__ == "__main__":
    # Initialize feeds on startup
    app.logger.info("[PhishGuard] Initializing threat intelligence feeds...")
    download_phishtank_dataset()
    start_background_feeds()
    app.logger.info("[PhishGuard] Backend initialized successfully")
    
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
