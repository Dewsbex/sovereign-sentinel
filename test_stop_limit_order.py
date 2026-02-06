import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.34 - STOP-LIMIT ORDER MODULE
print("🚀 TESTING STOP-LIMIT ORDER...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    # Target: Danaher (DHR)
    # Stop-Limit triggers at stopPrice, but only executes up to limitPrice.
    # Price ~$257. Trigger at 285, execute up to 286.
    payload = {
        "ticker": "DHR_US_EQ",
        "quantity": 1.0,
        "stopPrice": 285.0,
        "limitPrice": 286.0,
        "timeValidity": "GOOD_TILL_CANCEL"
    }
    
    url = f"{base_url}/orders/stop_limit"
    
    print(f"📡 Sending Stop-Limit Order: {json.dumps(payload, indent=2)}")
    try:
        resp = requests.post(url, json=payload, auth=auth, timeout=15)
        print(f"📥 Response Code: {resp.status_code}")
        print(f"📄 Body: {resp.text}")

        final_msg = ""
        if resp.status_code == 200:
            final_msg = "✅ **STOP-LIMIT MODULE SUCCESS**\n\nPlaced 1.0 DHR @ $285 Stop / $286 Limit."
        else:
            final_msg = f"❌ **STOP-LIMIT MODULE FAILED**\n\nError: {resp.status_code}\nBody: `{resp.text}`"

        if token and chat_id:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                           data={"chat_id": chat_id, "text": final_msg, "parse_mode": "Markdown"})

    except Exception as e:
        print(f"❌ Exception: {e}")
