import os
import requests
import json
from requests.auth import HTTPBasicAuth

# LIVE TEST SCRIPT
# This script will attempt to place a real order using the new credentials.
# Target: Citigroup (C_US_EQ)
# Quantity: 0.1 shares
# Intent: Verify API Key/Secret are working for TRADING.

print("🚀 STARTING LIVE TRADE TEST...")

# 1. Get Secrets from Env (Simulated as they would be in Cloud)
# In local test, we assume user keeps them in .env or we warn them.
# The user asked me to "test by placing a buy order now".
# Since I don't have the user's secret keys locally (they are in Cloudflare/GitHub Secrets),
# I CANNOT run this locally.

# HOWEVER, I can create this script, commit it, and run it via a manual workflow dispatch 
# that injects the new keys.

# But wait, the user says "please test by placing a buy order now".
# If I can't run it locally, I must use the Cloud.

# I will create a dedicated test workflow for this.

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY')
    t212_secret = os.getenv('T212_API_SECRET')
    
    if not t212_key or not t212_secret:
        print("❌ ERROR: Missing T212_API_KEY or T212_API_SECRET")
        exit(1)
        
    print(f"DEBUG: T212_API_KEY env present: {bool(t212_key)}")
    print(f"DEBUG: T212_API_SECRET env present: {bool(t212_secret)}")
    
    if not t212_key or not t212_secret:
        print("❌ ERROR: Missing T212_API_KEY or T212_API_SECRET in environment!")
        print("DIAGNOSTIC: Please ensure you added 'T212_API_Trade_Key' and 'T212_API_Trade_Secret' to GitHub->Settings->Secrets->Actions.")
        exit(1)
        
    print(f"🔑 Credentials detected. Testing endpoints...")
    
    endpoints = {
        "LIVE": "https://live.trading212.com/api/v0/equity/account/cash",
        "DEMO": "https://demo.trading212.com/api/v0/equity/account/cash"
    }
    
    success = False
    for name, url in endpoints.items():
        print(f"📡 Testing {name}: {url}...")
        try:
            auth = HTTPBasicAuth(t212_key, t212_secret)
            resp = requests.get(url, auth=auth, timeout=10)
            print(f"📥 {name} Response: {resp.status_code}")
            
            if resp.status_code == 200:
                print(f"✅ CONNECTION SUCCESS on {name}!")
                print(f"📄 Data: {resp.json()}")
                success = True
                break
            elif resp.status_code == 401:
                print(f"⚠️ {name} rejected (401 Unauthorized).")
            else:
                print(f"ℹ️ {name} other response: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"❌ {name} EXCEPTION: {e}")

    if not success:
        print("\n❌ FINAL VERDICT: Both LIVE and DEMO rejected these credentials.")
    else:
        print("\n🚀 VERDICT: Credentials are WORKING. Proceeding to place Test Order...")
        
        # Determine which endpoint worked
        target = "live" if "live" in url else "demo"
        trade_url = f"https://{target}.trading212.com/api/v0/equity/orders/limit"
        
        # Place the safe limit order
        ticker = "C"
        qty = 0.1
        price = 50.0 # Secure price, well below market
        
        payload = {
            "instrumentCode": f"{ticker}_US_EQ",
            "quantity": qty,
            "limitPrice": price,
            "timeValidity": "DAY"
        }
        
        print(f"📡 Sending LIMIT order to {trade_url}...")
        auth = HTTPBasicAuth(t212_key, t212_secret)
        trade_resp = requests.post(trade_url, json=payload, auth=auth, timeout=10)
        
        print(f"📥 Trade Response Code: {trade_resp.status_code}")
        print(f"📄 Trade Response Body: {trade_resp.text}")
        
        if trade_resp.status_code == 200:
            print(f"✅ SUCCESS! 0.1 shares of {ticker} queued at ${price}.")
            
            # Send Telegram Ping
            token = os.getenv('TELEGRAM_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            if token and chat_id:
                msg = f"🚀 **V32.16 LIVE TEST SUCCESS**\n\nTriggered 0.1 shares of Citigroup (C) @ $50.00 Limit.\nEndpoint: {target.upper()}"
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
        else:
            print("❌ TRADE REJECTED by API logic (Expected if market closed/min qty issues).")


