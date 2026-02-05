import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.18 - FORENSIC AUTH & TRADE TEST
print("🚀 STARTING FORENSIC TEST...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY')
    t212_secret = os.getenv('T212_API_SECRET')
    
    if not t212_key:
        print("❌ ERROR: Missing T212_API_KEY")
        exit(1)
        
    print(f"🔍 DEBUG: Key starts with: {t212_key[:5]}...")
    print(f"🔍 DEBUG: Secret present: {bool(t212_secret)}")
    
    # We will test 4 combinations:
    # 1. LIVE + Basic Auth (v0)
    # 2. DEMO + Basic Auth (v0)
    # 3. LIVE + Header Auth (v1 style)
    # 4. DEMO + Header Auth (v1 style)
    
    accounts = ["live", "demo"]
    auth_methods = ["BASIC", "HEADER"]
    
    success_config = None
    
    for acc in accounts:
        for method in auth_methods:
            url = f"https://{acc}.trading212.com/api/v0/equity/account/cash"
            print(f"\n📡 Testing {acc.upper()} with {method}...")
            
            headers = {}
            auth = None
            
            if method == "BASIC":
                if not t212_secret:
                    print("⏩ Skipping BASIC (Missing Secret)")
                    continue
                auth = HTTPBasicAuth(t212_key, t212_secret)
            else:
                # T212 v1 / Header only style
                headers = {"Authorization": t212_key}
            
            try:
                resp = requests.get(url, auth=auth, headers=headers, timeout=10)
                print(f"📥 Response: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"✅ SUCCESS! Found working config: {acc}/{method}")
                    print(f"📄 Account Data: {resp.json()}")
                    success_config = (acc, method, url.replace("/account/cash", ""))
                    break
                else:
                    print(f"📄 Message: {resp.text}")
            except Exception as e:
                print(f"❌ Exception: {e}")
        
        if success_config:
            break

    if not success_config:
        print("\n❌ ALL AUTH COMBINATIONS FAILED.")
        print("ACTION: Please double check your T212 API settings.")
        print("1. Did you enable 'Read' and 'Trade' permissions?")
        print("2. Did you disable 'IP restrictions'?")
        print("3. Are you using a 'Trading 212 Beta' API Key?")
        exit(1)

    # If we found a working config, attempt the 1 share buy.
    acc_type, auth_type, base_url = success_config
    print(f"\n🚀 Proceeding with TRADE test using {acc_type}/{auth_type}...")
    
    trade_url = f"{base_url}/orders/market"
    payload = {
        "instrumentCode": "C_US_EQ",
        "quantity": 1.0
    }
    
    headers = {}
    auth = None
    if auth_type == "BASIC":
        auth = HTTPBasicAuth(t212_key, t212_secret)
    else:
        headers = {"Authorization": t212_key}

    print(f"📡 Sending MARKET Order to {trade_url}...")
    trade_resp = requests.post(trade_url, json=payload, auth=auth, headers=headers, timeout=10)
    
    print(f"📥 Trade Response Code: {trade_resp.status_code}")
    print(f"📄 Trade Response Body: {trade_resp.text}")
    
    if trade_resp.status_code == 200:
        print("✅ SUCCESS! 1 share of Citigroup ordered.")
        # Telegram notification
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if token and chat_id:
            msg = f"🚀 **V32.18 AUTH FIXED**\nFound working config: {acc_type}/{auth_type}\nTrade Placed: 1.0 Citigroup (C)"
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": msg})
    else:
        print("ℹ️ Order failed but Auth is GOOD. Check T212 for instrument or market hours.")
