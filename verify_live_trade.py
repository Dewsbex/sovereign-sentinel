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
        
    print(f"🔑 Credentials Loaded (Key: {t212_key[:4]}***)")
    
    # 2. Construct Payload (Using LIMIT order for safety/queuing)
    ticker = "C" # Citigroup
    qty = 0.1
    price = 50.0 # Way below market ($65+), so it wont fill, just Pending.
    
    payload = {
        "instrumentCode": f"{ticker}_US_EQ",
        "quantity": qty,
        "limitPrice": price,
        "timeValidity": "DAY"
    }
    
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    # 3. Send Request
    url = "https://live.trading212.com/api/v0/equity/orders/limit"
    print(f"📡 Sending POST to {url}...")
    
    try:
        auth = HTTPBasicAuth(t212_key, t212_secret)
        resp = requests.post(url, json=payload, auth=auth, timeout=10)
        
        print(f"📥 Response Code: {resp.status_code}")
        print(f"📄 Response Body: {resp.text}")
        print(f"📄 Response Headers: {dict(resp.headers)}")
        
        if resp.status_code == 200:
            print("✅ SUCCESS! Limit Order Placed (Pending).")
        else:
            print("❌ FAILURE! API rejected order.")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
