import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.22 - NUE TRADING TEST
print("🚀 STARTING NUE TEST...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    
    if not t212_key:
        print("❌ ERROR: T212_API_KEY is empty.")
        exit(1)

    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"

    # Step 1: Find NUE Code
    print("📡 Step 1: Finding exact code for NUE...")
    nue_code = "NUE_US_EQ" # Default guess
    try:
        r = requests.get(f"{base_url}/instruments", auth=auth, timeout=30)
        if r.status_code == 200:
            instruments = r.json()
            matches = [i for i in instruments if i.get('ticker') == 'NUE']
            if matches:
                nue_code = matches[0].get('id')
                print(f"✅ Found NUE Code: {nue_code}")
            else:
                print("⚠️ NUE not found in simple ticker search. Checking names...")
                matches = [i for i in instruments if "Nucor" in i.get('name', '')]
                if matches:
                    nue_code = matches[0].get('id')
                    print(f"✅ Found Nucor Code: {nue_code}")
        else:
            print(f"❌ Failed to fetch instruments: {r.status_code}")
    except Exception as e:
        print(f"❌ Discovery Exception: {e}")

    # Step 2: Place Limit Order for NUE
    # Market is closed, so we use a safe Limit price.
    # NUE is ~$150-160. We'll use $100.
    print(f"\n🚀 Step 2: Placing Order for {nue_code}...")
    trade_url = f"{base_url}/orders/limit"
    
    payload = {
        "instrumentCode": nue_code,
        "quantity": 1.0,
        "limitPrice": 100.0,
        "timeValidity": "GTC" # Good Till Cancelled since it's waiting
    }
    
    print(f"📡 Sending Payload: {json.dumps(payload, indent=2)}")
    trade_resp = requests.post(trade_url, json=payload, auth=auth, timeout=10)
    
    print(f"📥 Response Code: {trade_resp.status_code}")
    print(f"📄 Response Body: {trade_resp.text}")
    
    if trade_resp.status_code == 200:
        print("\n✅ SUCCESS! NUE order is now waiting.")
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if token and chat_id:
            msg = f"✅ **NUE TRADING TEST SUCCESS**\n\nMethod: v0 Basic\nTicker: {nue_code}\nOrder: 1.0 share @ $100 Limit."
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": msg})
    else:
        print("\n❌ FINAL ATTEMPT FAILED.")
        print("Note: If error is 'Invalid payload', T212 might require float values or specific fields.")
