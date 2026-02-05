import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.16 - LIVE TRADING VERIFIER (RE-CLEANED)
print("🚀 STARTING LIVE TRADE TEST...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY')
    t212_secret = os.getenv('T212_API_SECRET')
    
    if not t212_key or not t212_secret:
        print("❌ ERROR: Missing T212_API_KEY or T212_API_SECRET in environment!")
        exit(1)
        
    print(f"🔑 Credentials detected. Testing endpoints...")
    
    endpoints = {
        "LIVE": "https://live.trading212.com/api/v0/equity/account/cash",
        "DEMO": "https://demo.trading212.com/api/v0/equity/account/cash"
    }
    
    success = False
    working_url = ""
    for name, url in endpoints.items():
        print(f"📡 Testing {name}: {url}...")
        try:
            auth = HTTPBasicAuth(t212_key, t212_secret)
            resp = requests.get(url, auth=auth, timeout=10)
            if resp.status_code == 200:
                print(f"✅ CONNECTION SUCCESS on {name}!")
                success = True
                working_url = url
                break
            else:
                print(f"ℹ️ {name} response: {resp.status_code}")
        except Exception as e:
            print(f"❌ {name} EXCEPTION: {e}")

    if not success:
        print("\n❌ FINAL VERDICT: Both LIVE and DEMO rejected these credentials.")
    else:
        print("\n🚀 VERDICT: Credentials are WORKING. Proceeding to place Test Order...")
        
        target = "live" if "live" in working_url else "demo"
        trade_url = f"https://{target}.trading212.com/api/v0/equity/orders/limit"
        
        # CITIGROUP (C) - 1 Share @ $50 Limit
        ticker = "C"
        qty = 1.0
        price = 50.0 
        
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
            print(f"✅ SUCCESS! {qty} share of {ticker} queued at ${price}.")
            
            # Telegram Ping
            token = os.getenv('TELEGRAM_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            if token and chat_id:
                msg = f"🚀 **V32.16 LIVE TEST SUCCESS**\n\nPlaced 1.0 shares of Citigroup (C) @ $50.00 Limit.\nEndpoint: {target.upper()}\n\n*Check T212 'Pending Orders' list.*"
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
        else:
            print(f"❌ TRADE FAILED ({trade_resp.status_code}). See response body above.")
