import os
import requests
import json
import base64
from requests.auth import HTTPBasicAuth

# V32.19 - EXHAUSTIVE FORENSIC TEST (v0, v1, v2 + Multi-Auth)
print("🚀 STARTING EXHAUSTIVE FORENSIC TEST...")

def test_config(name, url, headers=None, auth=None):
    print(f"📡 Testing {name}...")
    try:
        resp = requests.get(url, headers=headers, auth=auth, timeout=10)
        print(f"📥 Response: {resp.status_code}")
        if resp.status_code == 200:
            print(f"✅ SUCCESS on {name}!")
            print(f"📄 Data: {resp.json()}")
            return True
        elif resp.status_code == 401:
            print(f"❌ 401 Unauthorized")
        else:
            print(f"🔹 {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"⚠️ Exception: {e}")
    return False

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    
    if not t212_key:
        print("❌ ERROR: T212_API_KEY is empty.")
        exit(1)

    print(f"🔍 DEBUG: Key Length: {len(t212_key)}")
    print(f"🔍 DEBUG: Secret Length: {len(t212_secret)}")

    # 1. THE BASIC AUTH TEST (Standard v0)
    # Most likely for older keys
    if t212_secret:
        test_config("LIVE v0 (Basic)", "https://live.trading212.com/api/v0/equity/account/cash", auth=HTTPBasicAuth(t212_key, t212_secret))
        test_config("DEMO v0 (Basic)", "https://demo.trading212.com/api/v0/equity/account/cash", auth=HTTPBasicAuth(t212_key, t212_secret))

    # 2. THE MODERN HEADER TEST (Standard v1)
    # T212 V1 uses the legacy key in the 'Authorization' header directly.
    headers_raw = {"Authorization": t212_key}
    test_config("LIVE v1 (Raw Header)", "https://live.trading212.com/api/v1/equity/account/cash", headers=headers_raw)
    test_config("DEMO v1 (Raw Header)", "https://demo.trading212.com/api/v1/equity/account/cash", headers=headers_raw)

    # 3. THE BEARER TEST (Some Beta keys use this)
    headers_bearer = {"Authorization": f"Bearer {t212_key}"}
    test_config("LIVE v1 (Bearer)", "https://live.trading212.com/api/v1/equity/account/cash", headers=headers_bearer)

    # 4. THE METADATA TEST (Check if we can even talk to the server)
    print("\n🌐 Step 2: Checking Server Reachability...")
    try:
        r = requests.get("https://live.trading212.com/api/v0/equity/metadata/exchanges", timeout=5)
        print(f"🌍 Live Metadata Status: {r.status_code} (Should be 200)")
    except:
        print("🌍 Live Server UNREACHABLE")

    print("\n--- FINAL VERDICT ---")
    print("If all 401s above:")
    print("1. REGENERATE NEW KEYS in T212 (Settings -> API).")
    print("2. DISBALE 'IP Restriction' (This is the #1 cause of 401s on GitHub).")
    print("3. Ensure you are copying the FULL strings with no extra spaces.")
