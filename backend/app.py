"""
PhishGuard AI  Flask Backend
Hybrid phishing detection engine combining a Random Forest ML model
with a 16+ rule heuristic scoring system, explainable AI chat endpoint,
URL normalization, edge-case handling, and threat intelligence checks.
"""

import os
import re
import socket
import datetime
import logging
import threading
import time
import io
import csv
from urllib.parse import urlparse, unquote
import secrets
from functools import wraps

from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import joblib
import pandas as pd
import requests
from dotenv import load_dotenv
load_dotenv()

# Import database module
from database import (
    initialize_database, log_scan_result, track_user, is_user_banned,
    get_stats, get_recent_scans, get_users, get_banned_users,
    ban_user, unban_user, get_detection_stats
)

# ---------------------------------------------------------------------------
#  App Setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {
        "origins": [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
        ],
        "supports_credentials": True,
        "allow_headers": ["Content-Type"],
        "methods": ["GET", "POST", "OPTIONS"]
    }}
)
app.logger.setLevel(logging.INFO)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "phishguard123"

MODEL_PATH = os.getenv("MODEL_PATH", "phish_model.joblib")
model = joblib.load(MODEL_PATH)

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
    r'(?:[A-Z]{2,63}|XN--[A-Z0-9]{1,59}|localhost)'
    r'(?::\d{1,5})?'
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
def _strip_www(domain):
    """Strip leading 'www.' prefix so www.example.com == example.com for feature purposes."""
    if domain.startswith("www."):
        return domain[4:]
    return domain


def extract_features(url):
    parsed = urlparse(url)
    raw_domain = parsed.hostname or ""
    # Normalise: treat www.foo.com identically to foo.com for ML features
    domain = _strip_www(raw_domain)
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
    """SSL certificate age detection - DISABLED"""
    result = {
        "status": "unavailable",
        "certificate_age_days": None,
        "risk": 0,
        "details": "SSL certificate age detection disabled",
    }
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


def check_domain_resolution(url):
    parsed = urlparse(url)
    domain = (parsed.hostname or "").strip().lower()
    result = {
        "status": "ok",
        "resolved": True,
        "risk": 0,
        "details": "Domain resolves normally",
        "ip_count": 0,
    }

    if not domain:
        result["status"] = "error"
        result["resolved"] = False
        result["risk"] = 40
        result["details"] = "No domain to resolve"
        return result

    # Raw IPv4 hosts bypass DNS and are already handled by other heuristics.
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
        result["details"] = "Raw IP host provided (DNS not required)"
        return result

    cache_key = "dns_resolution::" + domain
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        addr_info = socket.getaddrinfo(domain, None)
        unique_ips = {item[4][0] for item in addr_info if item and len(item) > 4 and item[4]}
        result["ip_count"] = len(unique_ips)
        if not unique_ips:
            result["resolved"] = False
            result["risk"] = 60
            result["details"] = "Domain has no usable DNS records"
            _cache_set(cache_key, result, 10 * 60)
            return result

        result["details"] = "Domain resolves to " + str(len(unique_ips)) + " IP address(es)"
        _cache_set(cache_key, result, 30 * 60)
        return result
    except socket.gaierror as ex:
        code = getattr(ex, "errno", None)
        result["resolved"] = False
        if code in (socket.EAI_NONAME, socket.EAI_NODATA):
            result["risk"] = 70
            result["details"] = "Domain does not resolve (NXDOMAIN/no DNS record)"
        elif code == socket.EAI_AGAIN:
            result["risk"] = 35
            result["details"] = "Temporary DNS failure during lookup"
        else:
            result["risk"] = 55
            result["details"] = "DNS lookup failed"
        _cache_set(cache_key, result, 10 * 60)
        return result
    except Exception as ex:
        app.logger.warning("[PhishGuard] DNS resolution check failed for %s: %s", domain, str(ex))
        result["resolved"] = False
        result["risk"] = 45
        result["details"] = "DNS resolution check failed"
        _cache_set(cache_key, result, 5 * 60)
        return result


def check_illegal_blocked_sites(url):
    """Check against known illegal, copyright-infringing, or commonly blocked domains"""
    parsed = urlparse(url)
    domain = (parsed.hostname or "").strip().lower()
    
    result = {
        "status": "ok",
        "is_blocked": False,
        "risk": 0,
        "details": "Not in blocked list",
        "reason": None,
    }
    
    if not domain:
        return result

    # Skip trusted domains
    if is_trusted_domain(domain):
        result["details"] = "Trusted domain - blocklist check skipped"
        return result

    # Known illegal/blocked sites database
    # Includes: file-sharing (piracy), torrent, malware distribution, phishing platforms
    BLOCKED_DOMAINS = {
        # File-sharing / Piracy platforms (India-blocked, global known malicious)
        "exoshare.com", "exoshare.co", "exoshare.net",
        "indishare.com", "indishare.net", "indishare.io",
        "alfafile.net", "alfafile.org", "alfafile.co",
        "nitroflare.com", "nitroflare.net", "nitroflare.io",
        "uploadrocket.net", "uploadrocket.org", "uploadrocket.io",
        "loadus.net", "loadus.io", "loadus.org",
        "uploading.site", "uploading.org", "uploading.net",
        "depositfiles.com", "datafilehost.com", "dailyuploads.net",
        
        # Torrent sites
        "thepiratebay.org", "thepiratebay.com", "thepiratebay.vip",
        "torrentdownload.com", "torrentdownload.net",
        "torcache.net", "torrar.com",
        "kickasstorrents.com", "kickass.to",
        "zoink.it", "torlock.com",
        "rarbg.to", "rarbg.com",
        "1337x.to", "1337x.am",
        "eztv.io", "eztv.ag",
        "yify-torrent.com", "yts.lt",
        
        # Malware / Exploit distributions
        "exploitdb.com", "exploit.jp",
        
        # Known phishing / spam platforms (platforms often abused)
        "free-logins.com", "free-password.com",
        "account-verify.net", "verify-account.net",
        "confirm-identity.com", "validate-account.com",
        
        # Additional commonly blocked in India and other regions
        "bigfile.to", "bigfile.ws",
        "novafile.com", "novafile.net",
        "extratorrents.cc", "extratorrent.cc",
        "demonoid.pw", "demonoid.io",
        "isohunt.com", "isohunt.to",
        "torrentcreeper.com",
        "fileserve.com", "filesonic.com",
        "fshare.vn", "tusfiles.net",
    }
    
    BLOCKED_KEYWORDS = [
        "rapidshare", "megaupload", "hotfile", "mediafire", "uploaded.net",
        "torrent", "pirate", "warez", "crack", "keygen", "serial", "license",
        "movie-downloads", "download-free", "free-movies", "free-tv",
    ]
    
    cache_key = "blocked_sites::" + domain
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    
    # Exact domain match
    if domain in BLOCKED_DOMAINS:
        result["is_blocked"] = True
        result["risk"] = 80
        result["details"] = "Domain is on illegal/blocked sites list"
        result["reason"] = "Known piracy, file-sharing, or malware distribution platform"
        _cache_set(cache_key, result, 60 * 60)
        return result
    
    # Subdomain match (e.g., sub.exoshare.com)
    for blocked in BLOCKED_DOMAINS:
        if domain.endswith("." + blocked):
            result["is_blocked"] = True
            result["risk"] = 80
            result["details"] = "Subdomain of blocked domain: " + blocked
            result["reason"] = "Known piracy or malware distribution platform"
            _cache_set(cache_key, result, 60 * 60)
            return result
    
    # Keyword-based detection for common patterns
    domain_lower = domain.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in domain_lower:
            result["is_blocked"] = True
            result["risk"] = 65
            result["details"] = "Domain matches illegal/suspicious keyword: " + keyword
            result["reason"] = "Pattern matches known piracy/malware distribution"
            _cache_set(cache_key, result, 60 * 60)
            return result
    
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

    # Rule 8: Too many subdomains (strip leading www. -- it is never suspicious)
    sub_domain_check = _strip_www(domain)
    sub_count = max(sub_domain_check.count(".") - 1, 0)
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
        "domain_resolution": check_domain_resolution(url),
        "illegal_blocked_sites": check_illegal_blocked_sites(url),
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
        checks["phishtank"].get("found"),
        checks["openphish"].get("found"),
    ])

    dns_unresolved = not bool(checks["domain_resolution"].get("resolved", True))
    dns_risk = int(checks["domain_resolution"].get("risk", 0) or 0)

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

    # DNS override: unresolved NXDOMAIN-like domains are high risk for untrusted targets.
    if dns_unresolved and dns_risk >= 60 and not is_trusted_domain(parsed_domain):
        is_phishing = True
        normalized_level = "PHISHING"
        risk_score = max(risk_score, 70)
        dns_detail = checks["domain_resolution"].get("details", "Domain resolution failure")
        dns_flag = "Domain resolution risk: " + str(dns_detail)
        if dns_flag not in all_flags:
            all_flags.append(dns_flag)

    # BLOCKLIST override: Known illegal/banned sites are always flagged as phishing
    is_blocked = checks.get("illegal_blocked_sites", {}).get("is_blocked", False)
    blocked_risk = int(checks.get("illegal_blocked_sites", {}).get("risk", 0) or 0)
    if is_blocked and blocked_risk >= 65:
        is_phishing = True
        normalized_level = "PHISHING"
        risk_score = max(risk_score, 78)
        blocked_detail = checks["illegal_blocked_sites"].get("details", "Domain on blocklist")
        blocked_reason = checks["illegal_blocked_sites"].get("reason", "Illegal/banned site")
        blocked_flag = f"Blocklist match: {blocked_detail} -- {blocked_reason}"
        if blocked_flag not in all_flags:
            all_flags.append(blocked_flag)

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
    user_id = data.get("user_id", f"user_{request.remote_addr}").strip()

    if not raw_url:
        return jsonify({"error": "No URL provided"}), 400

    # Check if user is banned
    if is_user_banned(user_id):
        return jsonify({"error": "User is banned", "status": "blocked"}), 403

    # Track user activity
    try:
        track_user(user_id, request.remote_addr)
    except Exception as e:
        app.logger.error(f"Error tracking user: {str(e)}")

    url = normalize_url(raw_url)
    error = validate_url(url)
    if error:
        return jsonify({"error": error}), 400

    analysis = analyze_url(url)

    # Log scan result to database
    try:
        # Normalize result: "phishing" -> "Phishing", "legitimate" -> "Safe"
        result_normalized = "Phishing" if analysis["result"].lower() == "phishing" else "Safe"
        log_scan_result(
            url=analysis["url"],
            risk_score=analysis["risk_score"],
            result=result_normalized,
            source="extension",
            user_id=user_id,
            ip_address=request.remote_addr
        )
    except Exception as e:
        app.logger.error(f"Error logging scan: {str(e)}")

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


# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------------------------
#  Admin Authentication Endpoints
# ---------------------------------------------------------------------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    """Admin login endpoint."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        username = data.get("username", "")
        password = data.get("password", "")
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return jsonify({"success": True, "message": "Login successful"})
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    # GET request
    if 'admin_logged_in' in session:
        return jsonify({"status": "already_logged_in"})
    
    return jsonify({"status": "login_page"})


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    """Admin logout endpoint."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})


# ---------------------------------------------------------------------------
#  Admin API Endpoints
# ---------------------------------------------------------------------------
@app.route("/admin/stats", methods=["GET"])
@admin_required
def admin_stats():
    """Get system statistics."""
    try:
        stats = get_stats()
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/recent-scans", methods=["GET"])
@admin_required
def admin_recent_scans():
    """Get recent scan results."""
    try:
        limit = request.args.get("limit", 50, type=int)
        scans = get_recent_scans(limit=limit)
        return jsonify({"scans": scans, "count": len(scans)})
    except Exception as e:
        app.logger.error(f"Error fetching recent scans: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/users", methods=["GET"])
@admin_required
def admin_users():
    """Get all users."""
    try:
        limit = request.args.get("limit", 100, type=int)
        users = get_users(limit=limit)
        return jsonify({"users": users, "count": len(users)})
    except Exception as e:
        app.logger.error(f"Error fetching users: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/banned-users", methods=["GET"])
@admin_required
def admin_banned_users():
    """Get banned users."""
    try:
        limit = request.args.get("limit", 100, type=int)
        banned = get_banned_users(limit=limit)
        return jsonify({"banned_users": banned, "count": len(banned)})
    except Exception as e:
        app.logger.error(f"Error fetching banned users: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/ban-user", methods=["POST"])
@admin_required
def admin_ban_user():
    """Ban a user."""
    try:
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id", "")
        reason = data.get("reason", "Admin action")
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        ban_user(user_id, reason)
        return jsonify({"success": True, "message": f"User {user_id} banned"})
    except Exception as e:
        app.logger.error(f"Error banning user: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/unban-user", methods=["POST"])
@admin_required
def admin_unban_user():
    """Unban a user."""
    try:
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id", "")
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        unban_user(user_id)
        return jsonify({"success": True, "message": f"User {user_id} unbanned"})
    except Exception as e:
        app.logger.error(f"Error unbanning user: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/detection-stats", methods=["GET"])
@admin_required
def admin_detection_stats():
    """Get detection statistics for charts."""
    try:
        stats = get_detection_stats()
        return jsonify({"stats": stats})
    except Exception as e:
        app.logger.error(f"Error fetching detection stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Initialize database
    app.logger.info("[PhishGuard] Initializing database...")
    initialize_database()
    
    # Initialize feeds on startup
    app.logger.info("[PhishGuard] Initializing threat intelligence feeds...")
    download_phishtank_dataset()
    start_background_feeds()
    app.logger.info("[PhishGuard] Backend initialized successfully")
    
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
