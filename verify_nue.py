import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.23 - NUE VERBOSE TEST
print("🚀 STARTING NUE VERBOSE TEST...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    # Pre-test notification check
    print(f"🔍 DEBUG: Telegram Token present: {bool(token)}")
    print(f"🔍 DEBUG: Telegram Chat ID present: {bool(chat_id)}")

    if not t212_key:
        print("❌ ERROR: T212_API_KEY is empty.")
        exit(1)

    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"

    # Step 1: Find NUE
    print("📡 Step 1: Finding exact code for NUE...")
    nue_code = "NUE_US_EQ"
    try:
        r = requests.get(f"{base_url}/instruments", auth=auth, timeout=30)
        if r.status_code == 200:
            instruments = r.json()
            matches = [i for i in instruments if i.get('ticker') == 'NUE']
            if matches:
                nue_code = matches[0].get('id')
                print(f"✅ Found NUE Code: {nue_code}")
        else:
            print(f"❌ Failed to fetch instruments: {r.status_code}")
    except Exception as e:
        print(f"❌ Discovery Exception: {e}")

    # Step 2: Place Order
    print(f"\n🚀 Step 2: Placing Order for {nue_code}...")
    trade_url = f"{base_url}/orders/limit"
    
    payload = {
        "instrumentCode": nue_code,
        "quantity": 1, # Try integer quantity for safety
        "limitPrice": 100.0,
        "timeValidity": "DAY" # Try DAY instead of GTC
    }
    
    print(f"📡 Sending Payload: {json.dumps(payload, indent=2)}")
    trade_resp = requests.post(trade_url, json=payload, auth=auth, timeout=10)
    
    print(f"📥 Response Code: {trade_resp.status_code}")
    print(f"📄 Response Body: {trade_resp.text}")
    
    final_status = "FAILED"
    if trade_resp.status_code == 200:
        print("\n✅ SUCCESS!")
        final_status = f"SUCCESS (Order ID: {trade_resp.json().get('orderId')})"
    else:
        print("\n❌ FAILED.")
        final_status = f"FAILED: {trade_resp.status_code} - {trade_resp.text}"

    # Step 3: Send Mandatory Telegram Notification
    if token and chat_id:
        print("📡 Sending Telegram Pulse...")
        msg = f"🛰️ **NUE VERBOSE TEST REPORT**\n\n**Status**: {final_status}\n**Ticker**: {nue_code}\n**Auth**: v0 Basic (LIVE)"
        try:
            tr = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                               data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, 
                               timeout=10)
            print(f"📥 Telegram Response: {tr.status_code}")
        except Exception as te:
            print(f"❌ Telegram Exception: {te}")
    else:
        print("⚠️ Skipping Telegram: Missing Token/ChatID")
