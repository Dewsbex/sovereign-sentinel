import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.26 - INTELLIGENT ACTIVATOR
print("🚀 STARTING INTELLIGENT ACTIVATION...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"

    # 1. Search for Instrument Details
    target_ticker = "DHR" # Danaher
    print(f"📡 Searching for {target_ticker}...")
    
    inst_id = f"{target_ticker}_US_EQ"
    try:
        r = requests.get(f"{base_url}/instruments", auth=auth, timeout=30)
        if r.status_code == 200:
            instruments = r.json()
            matches = [i for i in instruments if i.get('ticker') == target_ticker]
            if matches:
                inst_id = matches[0].get('id')
                print(f"✅ Found exact ID: {inst_id}")
            else:
                print(f"⚠️ {target_ticker} not found. Defaulting to {inst_id}")
        else:
            print(f"❌ Failed to fetch symbols: {r.status_code}")
    except Exception as e:
        print(f"⚠️ Search error: {e}")

    # 2. Place Limit Order
    # We'll use a price closer to market to avoid "Too far" rejection
    # DHR is ~$257. Let's use $200.
    trade_url = f"{base_url}/orders/limit"
    
    payload = {
        "instrumentCode": inst_id,
        "quantity": 1,
        "limitPrice": 200.0,
        "timeValidity": "GTC" 
    }
    
    print(f"📡 Sending Order: {json.dumps(payload, indent=2)}")
    resp = requests.post(trade_url, json=payload, auth=auth, timeout=10)
    
    print(f"📥 Response: {resp.status_code}")
    print(f"📄 Body: {resp.text}")

    if resp.status_code == 200:
        print("\n✅ SUCCESS! LIVE TRADING ARMED.")
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if token and chat_id:
            msg = f"✅ **LIVE ACTIVATION SUCCESS**\n\nTicker: {inst_id}\nOrder: 1 share @ $200.00 Limit (GTC)\nStatus: PENDING"
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": msg})
    else:
        # Fallback: Try integer price if float fails? Or different validity
        print("🔄 Retrying with 'DAY' validity...")
        payload["timeValidity"] = "DAY"
        resp2 = requests.post(trade_url, json=payload, auth=auth, timeout=10)
        if resp2.status_code == 200:
            print("\n✅ SUCCESS (with DAY)!")
        else:
            print("\n❌ STILL FAILING. Checking for instrument restrictions...")
