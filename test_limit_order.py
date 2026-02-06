import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.31 - LIMIT ORDER MODULE
print("🚀 TESTING LIMIT ORDER...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    # Target: Danaher (DHR)
    # Payload matches the documentation for LIMIT orders
    payload = {
        "ticker": "DHR_US_EQ",
        "quantity": 1.0,
        "limitPrice": 190.0, # Safe limit below market
        "timeValidity": "GTC"
    }
    
    url = f"{base_url}/orders/limit"
    
    print(f"📡 Sending Limit Order: {json.dumps(payload, indent=2)}")
    try:
        resp = requests.post(url, json=payload, auth=auth, timeout=15)
        print(f"📥 Response Code: {resp.status_code}")
        print(f"📄 Body: {resp.text}")

        final_msg = ""
        if resp.status_code == 200:
            final_msg = "✅ **LIMIT ORDER MODULE SUCCESS**\n\nPlaced 1.0 DHR @ $190.00 Limit (GTC)."
        else:
            final_msg = f"❌ **LIMIT ORDER MODULE FAILED**\n\nError: {resp.status_code}\nBody: `{resp.text}`"

        if token and chat_id:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                           data={"chat_id": chat_id, "text": final_msg, "parse_mode": "Markdown"})

    except Exception as e:
        print(f"❌ Exception: {e}")
