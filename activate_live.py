import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.30 - DOC-COMPLIANT LIMIT ORDER (DHR)
print("🚀 STARTING DOC-COMPLIANT LIMIT TEST...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    # 2. Place Limit Order (Safe Price)
    # Payload adjusted for Official Spec v32.43
    instrument_code = "DHR_US_EQ" # Assuming instrument_code needs to be defined
    limit_price = 100.0 # Way below current price (~230) so it won't fill
    payload = {
        "ticker": instrument_code,
        "quantity": 1, # Buy 1 share
        "limitPrice": limit_price,
        "timeValidity": "GTC"
    }
    
    # Official endpoint for limit orders
    url = f"{base_url}/orders/limit"
    
    print(f"📡 Sending Official Limit Payload: {json.dumps(payload, indent=2)}")
    try:
        resp = requests.post(url, json=payload, auth=auth, timeout=15)
        print(f"📥 Response Code: {resp.status_code}")
        print(f"📄 Body: {resp.text}")

        final_msg = ""
        if resp.status_code == 200:
            final_msg = "✅ **LIMIT ORDER SUCCESS**\n\n1.0 share of DHR at $200.00 Limit (GTC) has been placed successfully."
        else:
            final_msg = f"❌ **LIMIT ORDER FAILED**\n\nError: {resp.status_code}\nBody: `{resp.text}`"

        # Telegram Report
        if token and chat_id:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                           data={"chat_id": chat_id, "text": final_msg, "parse_mode": "Markdown"})

    except Exception as e:
        print(f"❌ Exception: {e}")
