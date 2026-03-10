"""
PhishGuard AI  Flask Backend
Hybrid phishing detection engine combining a Random Forest ML model
with a 16+ rule heuristic scoring system, explainable AI chat endpoint,
URL normalization, edge-case handling, and WHOIS domain lookup.
"""

import os
import re
import socket
import datetime
from urllib.parse import urlparse, unquote

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd

# ---------------------------------------------------------------------------
#  App Setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

MODEL_PATH = os.getenv("MODEL_PATH", "phish_model.joblib")
model = joblib.load(MODEL_PATH)

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
    "github.com", "gitlab.com", "stackoverflow.com",
    "wikipedia.org", "wikimedia.org",
    "linkedin.com", "reddit.com",
    "netflix.com", "spotify.com", "twitch.tv", "tiktok.com", "discord.com",
    "zoom.us", "slack.com", "dropbox.com", "box.com",
    "paypal.com", "ebay.com", "etsy.com", "shopify.com",
    "yahoo.com", "ymail.com",
    "cloudflare.com", "cloudflare.net",
    "adobe.com", "notion.so",
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
]

SUSPICIOUS_TLDS = {
    ".xyz", ".tk", ".ml", ".ga", ".cf", ".gq",
    ".pw", ".top", ".zip", ".click", ".country", ".buzz", ".work", ".surf",
}

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly",
    "is.gd", "buff.ly", "short.link", "rebrand.ly", "cutt.ly",
}


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

    # Rule 4: Known URL shortener
    for shortener in URL_SHORTENERS:
        if shortener in domain:
            flags.append("URL shortener detected (" + shortener + ") -- real destination hidden")
            score += 15
            break

    # Rule 5: Suspicious keywords
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

    # ML probability
    features = extract_features(url)
    df = pd.DataFrame([features])
    try:
        proba = model.predict_proba(df)[0]
        ml_score = float(proba[1])
    except Exception:
        ml_score = 0.5

    # Heuristic engine
    flags, heuristic_score = run_heuristics(url)

    parsed_domain = urlparse(url).hostname or ""
    trusted = is_trusted_domain(parsed_domain)

    # Decision logic
    rule_probability = heuristic_score / 100.0
    combined_score = (0.6 * ml_score) + (0.4 * rule_probability)

    if trusted and heuristic_score == 0:
        is_phishing = False
        combined_score = ml_score * 0.20
    elif heuristic_score >= 40:
        is_phishing = True
        combined_score = max(combined_score, 0.50)
    elif ml_score >= 0.50:
        is_phishing = True
    elif combined_score >= 0.35:
        is_phishing = True
    else:
        is_phishing = False

    result = "phishing" if is_phishing else "legitimate"
    risk_level = get_risk_level(combined_score, is_phishing)

    return jsonify({
        "url":            url,
        "result":         result,
        "confidence":     round(combined_score * 100, 1),
        "ml_score":       round(ml_score * 100, 1),
        "rule_score":     heuristic_score,
        "combined_score": round(combined_score * 100, 1),
        "risk_level":     risk_level,
        "flags":          flags,
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
        "version": "2.0.0",
        "engine": "ML + Heuristic Hybrid",
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
