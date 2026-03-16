# Google Safe Browsing API - Troubleshooting Guide

## Changes Made

Fixed the Safe Browsing integration with the following improvements:

### 1. **Environment Variable Name Compatibility** ✅
- **Problem**: Code was only checking `GOOGLE_SAFE_BROWSING_API_KEY`
- **Fix**: Now checks both `GOOGLE_SAFE_BROWSING_API_KEY` and `GOOGLE_SAFE_BROWSING_KEY` (fallback)
- **Result**: Works with either variable name in .env

```python
GOOGLE_SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", os.getenv("GOOGLE_SAFE_BROWSING_KEY", "")).strip()
```

### 2. **Added Missing Threat Type** ✅
- **Before**: `["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"]`
- **After**: `["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"]`

### 3. **Improved Error Handling & Logging** ✅
- Specific handling for 403 (auth), 404 (endpoint), timeouts, and connection errors
- Detailed debug logging to identify exact failure points
- SSL verification explicitly set to True

### 4. **Created Configuration Files** ✅
- `.env.example` - Template with all required variables
- `test_safe_browsing.py` - Diagnostic tool to test API

---

## Quick Setup

### Step 1: Get Google Safe Browsing API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use existing one)
3. Navigate to **APIs & Services** → **Library**
4. Search for "Safe Browsing API"
5. Click **Enable**
6. Go to **APIs & Services** → **Credentials**
7. Create an **API Key**
8. Copy the API key

### Step 2: Create .env File

```bash
# In backend/ directory
cp .env.example .env
```

Then edit `.env` and add your API key:

```
GOOGLE_SAFE_BROWSING_API_KEY=YOUR_API_KEY_HERE
```

**OR** use the alternative variable name:

```
GOOGLE_SAFE_BROWSING_KEY=YOUR_API_KEY_HERE
```

### Step 3: Verify Setup

Run the diagnostic script:

```bash
cd backend
python test_safe_browsing.py
```

Expected output:
```
✓ API key loaded successfully
✓ Connection successful (HTTP 200)
✓ Clean
```

---

## Common Issues & Solutions

### Issue 1: "API key not configured"

**Symptoms**: Function returns status "unavailable"

**Causes**:
- .env file not found
- Variable name mismatch
- File not in correct directory

**Solution**:
```bash
# Check .env exists in backend/
ls -la backend/.env

# Check variable name
grep GOOGLE_SAFE_BROWSING backend/.env

# Reload environment
python test_safe_browsing.py
```

---

### Issue 2: "403 Authentication Error"

**Symptoms**: HTTP 403 response

**Causes**:
1. API key is incorrect
2. Safe Browsing API not enabled in Google Cloud
3. API key doesn't have permission
4. Project quota exceeded

**Solution**:
```bash
# Step 1: Verify API key is correct
cat backend/.env | grep GOOGLE_SAFE_BROWSING

# Step 2: Check Google Cloud Console
- Go to APIs & Services → Library
- Search "Safe Browsing API"
- Verify it shows "ENABLED"

# Step 3: Check credentials
- Go to APIs & Services → Credentials
- Verify your API key is listed
- Check Key Restrictions (should allow Safe Browsing)

# Step 4: Test with diagnostic tool
python test_safe_browsing.py
```

---

### Issue 3: "Connection Error" or "Timeout"

**Symptoms**: Timeout or connection refused errors

**Causes**:
- Network connectivity issues
- Firewall blocking requests
- Corporate proxy
- DNS issues

**Solution**:
```bash
# Test internet connectivity
ping 8.8.8.8

# Test connection to Google API
curl -v "https://safebrowsing.googleapis.com/v4/threatMatches:find?key=test"

# If behind proxy, set environment variables
export HTTP_PROXY=your.proxy.com:8080
export HTTPS_PROXY=your.proxy.com:8080

# Run diagnostic again
python test_safe_browsing.py
```

---

### Issue 4: "404 Endpoint Not Found"

**Symptoms**: HTTP 404 response

**Causes**:
- Incorrect endpoint URL
- API version changed

**Solution**: 
Endpoint should be exactly:
```
https://safebrowsing.googleapis.com/v4/threatMatches:find?key=YOUR_API_KEY
```

If incorrect, update app.py line ~645:
```python
endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find?key=" + GOOGLE_SAFE_BROWSING_API_KEY
```

---

## Testing URLs

Test the integration with known URLs:

```python
import requests

API_KEY = "YOUR_KEY_HERE"
endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={API_KEY}"

# Safe URL (shouldn't be flagged)
test_payload = {
    "client": {"clientId": "phishguard-ai", "clientVersion": "3.0"},
    "threatInfo": {
        "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
        "platformTypes": ["ANY_PLATFORM"],
        "threatEntryTypes": ["URL"],
        "threatEntries": [{"url": "https://www.google.com"}],
    },
}

resp = requests.post(endpoint, json=test_payload)
print(resp.status_code)
print(resp.json())
```

---

## Logging

Enable detailed logging in app.py to see Safe Browsing requests/responses:

```python
# In app.py, logging is already enabled at DEBUG level for:
app.logger.debug("[PhishGuard] Safe Browsing endpoint: %s", endpoint)
app.logger.debug("[PhishGuard] Safe Browsing response status: %d", resp.status_code)
app.logger.debug("[PhishGuard] Safe Browsing response data: %s", str(data)[:500])
```

To see debug logs, ensure Flask debug is enabled:
```
FLASK_DEBUG=true
```

Then check logs in terminal output.

---

## Deployment (Render)

When deploying to Render:

1. Set environment variables in Render dashboard:
   - Dashboard → Your Service → Environment
   - Add: `GOOGLE_SAFE_BROWSING_API_KEY=YOUR_KEY`

2. Verify Safe Browsing API is enabled in Google Cloud for your API key

3. Test deployment:
   ```bash
   curl "https://your-backend.onrender.com/health"
   ```

---

## Still Having Issues?

1. Run diagnostic script first:
   ```bash
   python backend/test_safe_browsing.py
   ```

2. Check logs for exact error message:
   ```bash
   cat backend/app.log  # if logging to file
   ```

3. Verify .env file is in correct location:
   ```bash
   pwd  # should be backend/
   ls -la .env
   ```

4. Read the error details carefully - they indicate the exact problem (403, 404, timeout, etc.)

5. Reference: [Google Safe Browsing API Docs](https://developers.google.com/safe-browsing/v4)
