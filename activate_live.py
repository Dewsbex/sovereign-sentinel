import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.27 - THE DEFINITIVE ACTIVATOR
print("🚀 STARTING DEFINITIVE ACTIVATION...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    auth = HTTPBasicAuth(t212_key, t212_secret)
    # The base path for metadata is /metadata/instruments
    base_url = "https://live.trading212.com/api/v0/equity"
    
    target_ticker = "DHR"
    print(f"📡 Step 1: Discovering exact ID for {target_ticker}...")
    
    found_id = f"{target_ticker}_US_EQ"
    try:
        # CORRECT METADATA ENDPOINT
        r = requests.get(f"{base_url}/metadata/instruments", auth=auth, timeout=30)
        if r.status_code == 200:
            instruments = r.json()
            matches = [i for i in instruments if i.get('ticker') == target_ticker]
            if matches:
                found_id = matches[0].get('id')
                print(f"✅ Found ID: {found_id}")
            else:
                print(f"⚠️ {target_ticker} not in list. Using fallback {found_id}")
        else:
            print(f"❌ Metadata Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"⚠️ Search error: {e}")

    # Step 2: Place Limit Order
    print(f"\n🚀 Step 2: Placing Order for {found_id}...")
    trade_url = f"{base_url}/orders/limit"
    
    # Try using full 'GOOD_TILL_CANCEL' string
    payload = {
        "instrumentCode": found_id,
        "quantity": 1.0,
        "limitPrice": 200.0,
        "timeValidity": "GOOD_TILL_CANCEL"
    }
    
    print(f"📡 Sending Payload: {json.dumps(payload, indent=2)}")
    resp = requests.post(trade_url, json=payload, auth=auth, timeout=15)
    
    print(f"📥 Response Code: {resp.status_code}")
    print(f"📄 Body: {resp.text}")

    final_msg = ""
    if resp.status_code == 200:
        print("\n✅ SUCCESS!")
        final_msg = f"✅ **LIVE ACTIVATION SUCCESS**\n\nTicker: `{found_id}`\nOrder: 1.0 @ $200.00\nStatus: PENDING"
    else:
        # Retry one last time with 'DAY' just in case
        print("🔄 Retrying with DAY validity...")
        payload["timeValidity"] = "DAY"
        resp2 = requests.post(trade_url, json=payload, auth=auth, timeout=15)
        if resp2.status_code == 200:
            final_msg = f"✅ **LIVE ACTIVATION SUCCESS (DAY)**\n\nTicker: `{found_id}`\nOrder: 1.0 @ $200.00"
        else:
            final_msg = f"❌ **LIVE ACTIVATION FAILED**\n\nError: {resp2.status_code}\nBody: `{resp2.text}`"

    # Step 3: Telegram Ping (Mandatory)
    if token and chat_id:
        print("📡 Sending Telegram Pulse...")
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                       data={"chat_id": chat_id, "text": final_msg, "parse_mode": "Markdown"})
