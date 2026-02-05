import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.17 - MARKET ORDER VERIFIER (CITIGROUP)
print("🚀 STARTING MARKET ORDER TEST...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY')
    t212_secret = os.getenv('T212_API_SECRET')
    
    if not t212_key or not t212_secret:
        print("❌ ERROR: Missing T212_API_KEY or T212_API_SECRET")
        exit(1)
        
    # 1. AUTH CHECK
    auth = HTTPBasicAuth(t212_key, t212_secret)
    cash_url = "https://live.trading212.com/api/v0/equity/account/cash"
    print(f"📡 Step 1: Checking Authentication...")
    auth_resp = requests.get(cash_url, auth=auth, timeout=10)
    
    if auth_resp.status_code != 200:
        print(f"❌ AUTH FAILED: {auth_resp.status_code} - {auth_resp.text}")
        exit(1)
    print("✅ AUTH SUCCESS!")

    # 2. MARKET ORDER (Shares only)
    # The user asked: "does api require price? or just number of shared?"
    # A MARKET order only requires quantity.
    ticker = "C" 
    qty = 1.0 # 1 Share
    
    # Note: T212 API usually rejects MARKET orders when market is closed.
    market_url = "https://live.trading212.com/api/v0/equity/orders/market"
    payload = {
        "instrumentCode": f"{ticker}_US_EQ",
        "quantity": qty
    }
    
    print(f"📡 Step 2: Sending MARKET Order (Qty: {qty}) to {market_url}...")
    trade_resp = requests.post(market_url, json=payload, auth=auth, timeout=10)
    
    print(f"📥 Trade Response Code: {trade_resp.status_code}")
    print(f"📄 Trade Response Body: {trade_resp.text}")
    
    if trade_resp.status_code == 200:
        print(f"✅ SUCCESS! 1 share of {ticker} ordered at market price.")
        # Telegram Ping
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if token and chat_id:
            msg = f"✅ **V32.17 TEST SUCCESS**\n\nOrdered 1.0 share of Citigroup (C) at Market Price."
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": msg})
    else:
        print("\nDIAGNOSTIC:")
        if "market is closed" in trade_resp.text.lower():
            print("💡 CAUSE: T212 does not allow MARKET orders while the market is closed.")
            print("💡 FIX: We must use a LIMIT order if testing tonight, or wait until tomorrow 14:30 GMT for Market orders.")
        else:
            print(f"💡 REASON: {trade_resp.text}")
