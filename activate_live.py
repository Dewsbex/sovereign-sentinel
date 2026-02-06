import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.28 - UK CURRENCY TEST (LLOY)
print("🚀 STARTING UK CURRENCY TEST...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    # Testing with a UK Stock to match "Main Account Currency" (GBP)
    target_ticker = "LLOY"
    print(f"📡 Step 1: Discovering exact ID for {target_ticker}...")
    
    found_id = "LLOY_L_EQ" # Standard T212 ID for Lloyds
    try:
        r = requests.get(f"{base_url}/metadata/instruments", auth=auth, timeout=30)
        if r.status_code == 200:
            instruments = r.json()
            matches = [i for i in instruments if i.get('ticker') == target_ticker]
            if matches:
                found_id = matches[0].get('id')
                print(f"✅ Found ID: {found_id}")
    except Exception as e:
        print(f"⚠️ Search error: {e}")

    # Step 2: Place Limit Order (GBP)
    print(f"\n🚀 Step 2: Placing Order for {found_id}...")
    trade_url = f"{base_url}/orders/limit"
    
    # We include both 'ticker' and 'instrumentCode' for maximum compatibility
    payload = {
        "ticker": found_id,
        "instrumentCode": found_id,
        "quantity": 10.0, # 10 shares of Lloyds (~£5.00)
        "limitPrice": 40.0, # 40p Limit (Current price ~53p)
        "timeValidity": "GOOD_TILL_CANCEL"
    }
    
    print(f"📡 Sending Payload: {json.dumps(payload, indent=2)}")
    resp = requests.post(trade_url, json=payload, auth=auth, timeout=15)
    
    print(f"📥 Response Code: {resp.status_code}")
    print(f"📄 Body: {resp.text}")

    final_msg = ""
    if resp.status_code == 200:
        final_msg = f"✅ **UK ACTIVATION SUCCESS**\n\nTicker: `{found_id}`\nOrder: 10 shares @ 40p\nStatus: PENDING"
    else:
        # Final retry with integer quantity
        print("🔄 Trying integer quantity...")
        payload["quantity"] = 10
        resp2 = requests.post(trade_url, json=payload, auth=auth, timeout=15)
        if resp2.status_code == 200:
            final_msg = f"✅ **UK ACTIVATION SUCCESS (Int)**\n\nTicker: `{found_id}`"
        else:
            final_msg = f"❌ **UK ACTIVATION FAILED**\n\nError: {resp2.status_code}\nBody: `{resp2.text}`"

    # Step 3: Telegram Ping
    if token and chat_id:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                       data={"chat_id": chat_id, "text": final_msg, "parse_mode": "Markdown"})
