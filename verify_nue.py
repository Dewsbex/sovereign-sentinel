import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.24 - NUE FORENSIC PAYLOAD TEST
print("🚀 STARTING NUE FORENSIC PAYLOAD TEST...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"

    # Step 1: Discover the EXACT ID T212 uses for NUE
    print("📡 Step 1: Finding exact ID for NUE...")
    valid_id = None
    try:
        r = requests.get(f"{base_url}/instruments", auth=auth, timeout=30)
        if r.status_code == 200:
            instruments = r.json()
            # Filter for NUE accurately
            matches = [i for i in instruments if i.get('ticker') == 'NUE' or i.get('name') == 'Nucor']
            if matches:
                valid_id = matches[0].get('id')
                print(f"✅ Found ID in T212 Database: `{valid_id}`")
            else:
                print("⚠️ NUE not found in database. Using default fallback.")
                valid_id = "NUE_US_EQ"
        else:
            print(f"❌ Failed to fetch list: {r.status_code}")
            valid_id = "NUE_US_EQ"
    except Exception as e:
        print(f"❌ Discovery Error: {e}")
        valid_id = "NUE_US_EQ"

    # Step 2: Attempt different payload variations
    # We'll try: 1.0 (float) vs 1 (int) and different timeValidity
    print(f"\n🚀 Step 2: Attempting Trade with ID: {valid_id}...")
    
    trade_url = f"{base_url}/orders/limit"
    
    # Variation 1: The standard format
    payload = {
        "instrumentCode": valid_id,
        "quantity": 1.0,
        "limitPrice": 100.0,
        "timeValidity": "DAY"
    }
    
    print(f"📡 Trying Payload: {json.dumps(payload)}")
    resp = requests.post(trade_url, json=payload, auth=auth, timeout=10)
    
    print(f"📥 Response Code: {resp.status_code}")
    print(f"📄 Body: {resp.text}")

    result_msg = ""
    if resp.status_code == 200:
        result_msg = f"✅ SUCCESS!\nPlaced 1.0 NUE at $100.\nID used: `{valid_id}`"
    else:
        # If it failed, try variation 2: Integer Quantity
        print("🔄 Retrying with Integer Quantity...")
        payload["quantity"] = 1
        resp2 = requests.post(trade_url, json=payload, auth=auth, timeout=10)
        if resp2.status_code == 200:
            result_msg = f"✅ SUCCESS (Int Qty)!\nPlaced 1 share NUE at $100.\nID used: `{valid_id}`"
        else:
            result_msg = f"❌ FAILED BOTH WAYS\nFinal Error: {resp2.status_code} - {resp2.text}\nID detected: `{valid_id}`"

    # Step 3: Telegram Report
    if token and chat_id:
        msg = f"🛰️ **NUE FORENSIC REPORT**\n\n{result_msg}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                       data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
