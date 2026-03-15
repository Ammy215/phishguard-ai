# PhishGuard AI - Quick Reference Guide

## API Endpoints

### POST /predict
**Analyze a URL and get threat intelligence**

**Request:**
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

**Response:**
```json
{
  "url": "https://example.com",
  "result": "phishing|legitimate",
  "confidence": 85.5,
  "ml_score": 78.2,
  "rule_score": 92,
  "combined_score": 85.5,
  "risk_level": "high",
  "risk_level_normalized": "SUSPICIOUS",
  "ml_prediction": "phishing",
  "risk_score": 85,
  "flags": [
    "Brand impersonation detected -- mimics 'paypal' (typosquatting/leet-speak)",
    "Domain resembles trusted brand 'paypal'"
  ],
  "checks": {
    "whois_age": {
      "status": "ok",
      "domain": "paypa1.com",
      "age_days": 45,
      "risk": 15,
      "details": "Domain is 45 days old (recently registered - moderate risk)"
    },
    "google_safe_browsing": {
      "status": "unavailable",
      "flagged": false,
      "risk": 0,
      "details": "API key not configured"
    },
    "phishtank": {
      "status": "ok",
      "found": false,
      "risk": 0,
      "details": "Not found in PhishTank"
    },
    "domain_similarity": {
      "status": "ok",
      "is_similar": true,
      "risk": 30,
      "details": "Domain resembles trusted brand 'paypal'",
      "matched_brand": "paypal",
      "similarity": 0.923
    },
    "redirects": {
      "status": "ok",
      "redirect_count": 1,
      "final_url": "https://paypa1.com/login",
      "risk": 0,
      "details": "Normal redirect count (1)"
    },
    "shortened_url": {
      "status": "ok",
      "is_shortened": false,
      "shortener": null,
      "expanded_url": "https://paypa1.com",
      "risk": 0,
      "details": "Not a known URL shortener"
    },
    "openphish": {
      "status": "ok",
      "found": false,
      "risk": 0,
      "details": "Not found in OpenPhish feed"
    },
    "urlhaus": {
      "status": "ok",
      "found": false,
      "risk": 0,
      "details": "Not found in URLHaus"
    }
  }
}
```

## Environment Variables

### Required
None - all checks degrade gracefully if API keys missing

### Recommended
```bash
# .env file in backend directory

# Google Safe Browsing (optional)
GOOGLE_SAFE_BROWSING_API_KEY=YOUR_API_KEY_HERE

# PhishTank (optional - API way)
PHISHTANK_API_KEY=YOUR_API_KEY_HERE

# PhishTank (optional - local CSV)
PHISHTANK_LOCAL_DB=/path/to/phishtank.csv

# Flask settings
FLASK_DEBUG=true
PORT=5000
CORS_ORIGINS=*

# Model path
MODEL_PATH=phish_model.joblib
```

## Threat Check Details

### 1. WHOIS Domain Age
- **Detects**: Very new domains (0-30 days = high risk)
- **Risk Score**: 0-25 points
- **Cache**: 12 hours
- **Dependencies**: `python-whois` (already installed)

### 2. Google Safe Browsing
- **Detects**: Known malware, phishing, unwanted software
- **Risk Score**: 60 if flagged, 0 otherwise
- **Cache**: 30 minutes
- **API Key**: `GOOGLE_SAFE_BROWSING_API_KEY`
- **Status**: Returns "unavailable" if key not set

### 3. PhishTank
- **Detects**: Registered phishing URLs
- **Risk Score**: 70 if found
- **Cache**: 20-30 minutes
- **Fallback**: Local CSV if API key missing
- **CSV Format**: Header must contain "url" column

### 4. OpenPhish Feed
- **Detects**: Active phishing URLs (real-time feed)
- **Risk Score**: 75 if found
- **Cache**: 1 hour
- **Source**: https://openphish.com/feed.txt
- **Status**: Gracefully handles feed download failures

### 5. URLHaus Malware DB
- **Detects**: Malware hosting, exploit kits, phishing
- **Risk Score**: 70 if found
- **Cache**: 30 minutes
- **API**: https://urlhaus-api.abuse.ch/v1/url/
- **Status**: Handles API failures gracefully

### 6. Redirect Chain Detection
- **Detects**: Suspicious redirect chains 
- **Risk Score**: 15 if >3 redirects, 30 if >5 redirects
- **Cache**: 10 minutes
- **Method**: Follows HTTP redirects (allows max 10 redirects)
- **Timeout**: 10 seconds

### 7. Domain Similarity (Brand Impersonation)
- **Detects**: Typosquatting and brand lookalikes
- **Trusted Brands**: paypal, google, amazon, facebook, microsoft, apple, netflix
- **Risk Score**: 30 if ≥0.88 similarity, 18 if ≥0.80 similarity
- **Algorithm**: Levenshtein distance with leet-speak normalization
- **Examples Detected**: 
  - `paypa1.com` → PayPal (similarity: 0.923)
  - `g00gle.com` → Google (similarity: 0.875)

### 8. Shortened URL Detection
- **Detects**: bit.ly, tinyurl.com, t.co, is.gd, ow.ly, goo.gl
- **Risk Score**: 10 if shortened
- **Cache**: 30 minutes
- **Feature**: Returns expanded URL
- **Method**: Follows redirects to get final destination

## Console Logging

Watch for `[PhishGuard]` prefixed logs:

```
[PhishGuard] WHOIS lookup: example.com
[PhishGuard] WHOIS result: 45 days, risk: 15
[PhishGuard] Google Safe Browsing check: https://example.com
[PhishGuard] PhishTank check (API): https://example.com
[PhishGuard] Downloading OpenPhish feed...
[PhishGuard] OpenPhish feed loaded: 25000 URLs
[PhishGuard] URLHaus check: https://example.com
[PhishGuard] Redirect detection: https://example.com
[PhishGuard] Redirect result: count=1, risk=0
```

## Error Handling

### Check Status Values
- **"ok"**: Check completed successfully
- **"error"**: Check attempted but failed (still safe to use)
- **"unavailable"**: Check not available (API key missing, library not installed)

### Pipeline Behavior
- **No Hard Failures**: If a check fails, others continue
- **Graceful Degradation**: Missing API keys → unavailable status
- **Risk Aggregation**: Check risks combine into overall score
- **Confirmed Threats**: If any check finds a threat (phishtank, openphish, urlhaus), result is immediately marked phishing

## Frontend Components

### Threat Intelligence Grid
- **Location**: Below detection flags
- **Layout**: 2-column grid (responsive)
- **Colors**:
  - 🟢 Green: Safe/Clean
  - 🟡 Yellow: Suspicious (2-3 redirects)
  - 🔴 Red: Phishing/Malware detected
  - ⚠️ Orange: Shortened URLs

### Click-through Details
- Each threat shows status, risk score, and human-readable explanation
- Similarity percentages displayed for brand impersonation
- Final URL shown for shortened link expansions

## Performance Tips

1. **Cache Strategy**: Check results cached by TTL
   - Same URL scanned twice within TTL = instant second result
   
2. **API Quotas**: Google Safe Browsing has daily limits
   - ~5 requests/second sustained
   - ~600 requests/minute burst limit
   
3. **Network Timeouts**:
   - WHOIS: No timeout (can be slow for some domains)
   - HTTP redirects: 10-second timeout
   - API calls: 8-second timeout
   
4. **Local Caching**: Consider running PhishTank CSV locally
   - Set `PHISHTANK_LOCAL_DB=/path/to/phishtank.csv`
   - Download CSV from: http://data.phishtank.com/data/online-valid.csv

## Troubleshooting

### Check fails with "error" status
1. Check backend logs for `[PhishGuard]` messages
2. Verify network connectivity (curl the API endpoint directly)
3. Check API key validity if applicable

### "unavailable" status
1. Verify required API key is set in .env
2. Verify `python-whois` installed: `pip list | grep whois`
3. This is expected - feature degrades gracefully

### Slow scans
1. Check cache - first scan is slower than subsequent ones
2. Monitor redirect chain checks (can take 10 seconds)
3. Consider running backend on same machine as frontend

### False ✅ Safe on known phishing URLs
1. Ensure at least one threat feed is configured
2. Check OpenPhish and PhishTank feeds are being downloaded
3. Verify API responses aren't cached from previous run
