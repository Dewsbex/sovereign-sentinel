# Trading 212 API Authentication Rules

> **⚠️ CRITICAL: DO NOT MODIFY THE AUTHENTICATION PATTERN WITHOUT READING THIS ENTIRE DOCUMENT**

## 🔒 Authentication Requirements

Trading 212 API **REQUIRES** HTTP Basic Authentication with **BOTH** credentials:

### Required Environment Variables
```bash
T212_API_KEY=your_api_key_here
T212_API_SECRET=your_api_secret_here
```

Both variables **MUST** be set in:
- Cloudflare Pages Environment Variables (for production)
- `.env` file (for local development)

## ✅ CORRECT Authentication Pattern

```python
from requests.auth import HTTPBasicAuth

# Load credentials
api_key = str(config.T212_API_KEY).strip()
api_secret = str(config.T212_API_SECRET).strip()

# Validate both are present
if not api_key or not api_secret:
    raise ValueError("Both T212_API_KEY and T212_API_SECRET are required")

# Create HTTP Basic Auth credentials
auth_credentials = HTTPBasicAuth(api_key, api_secret)

# Use in ALL API requests
headers = {
    "User-Agent": "Mozilla/5.0 SovereignSentinel/1.0",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers, auth=auth_credentials)
```

## ❌ INCORRECT Patterns (DO NOT USE)

### ❌ auth=None (Will fail with 401)
```python
# WRONG - This does not work!
response = requests.get(url, headers=headers, auth=None)
```

### ❌ API Key in Authorization header only
```python
# WRONG - Trading 212 does not accept this
headers = {
    "Authorization": api_key,  # Missing secret!
    ...
}
response = requests.get(url, headers=headers, auth=None)
```

### ❌ API Key in custom header
```python
# WRONG - Not the correct auth method
headers = {
    "X-API-Key": api_key,  # Trading 212 doesn't use this
    ...
}
```

### ❌ Bearer token
```python
# WRONG - Trading 212 uses Basic Auth, not Bearer
headers = {
    "Authorization": f"Bearer {api_key}",
    ...
}
```

## 📋 API Endpoints Used

All of these endpoints require proper authentication:

1. **Metadata**: `GET /api/v0/equity/metadata/instruments`
   - Returns currency codes, symbols, instrument types
   - Used for currency normalization (GBX → GBP conversion)

2. **Portfolio**: `GET /api/v0/equity/portfolio`
   - Returns all positions with quantities and current values
   - Critical for wealth calculation

3. **Account Cash**: `GET /api/v0/equity/account/cash`
   - Returns `free` (available) and `total` (including pending orders)
   - Use `total` for correct Total Wealth calculation

## 🔍 Testing Authentication

To verify authentication is working:

```python
# This should print: "[AUTH] Using HTTP Basic Auth (API_KEY:API_SECRET)"
# If you see warnings or errors, authentication is not configured correctly

python generate_static.py
```

Expected output:
```
      [AUTH] Using HTTP Basic Auth (API_KEY:API_SECRET)
      [DEBUG] Metadata: Loaded XXX instruments
      [DEBUG] Portfolio: Received XX positions
      [DEBUG] Cash: {'free': X.XX, 'total': X.XX, ...}
```

## 🚨 Symptoms of Broken Authentication

If you see these errors, authentication is broken:

```
[DEBUG] Metadata: Failed with status None
[DEBUG] Portfolio: Failed with status None
[DEBUG] Cash: Failed with status None
```

Or HTTP 401 Unauthorized errors.

## 📝 Historical Context

**Date**: January 26, 2026  
**Incident**: Authentication was accidentally changed to `auth=None` during rate limit debugging  
**Impact**: 2 days of downtime with 401 errors  
**Fix**: Commit `199d92c` - Restored proper HTTP Basic Auth  

## 🔗 Official Documentation

Trading 212 API Docs: https://t212public-api-docs.redoc.ly/

From their docs:
> "The API uses a secure key pair for authentication on every request. You must provide your API Key as the username and your API Secret as the password, formatted as an HTTP Basic Authentication header."

## 🛡️ Security Best Practices

1. **Never commit credentials to Git**
   - Keep `.env` in `.gitignore`
   - Use environment variables in production

2. **Rotate keys if exposed**
   - Generate new API keys in Trading 212 app
   - Update in Cloudflare and `.env`

3. **Test locally first**
   - Verify authentication works before deploying
   - Check Cloudflare logs after deployment

## ⚡ Rate Limiting

- Current implementation includes retry logic with exponential backoff
- Sleeps between requests to avoid 429 errors
- Do not remove delays without testing thoroughly

---

**Last Updated**: 2026-01-26  
**Maintained by**: Development team  
**DO NOT DELETE THIS FILE**
