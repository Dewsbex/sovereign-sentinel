import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.29 - DOC-COMPLIANT MARKET ORDER (DHR)
print("🚀 STARTING DOC-COMPLIANT MARKET TEST...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    # Using EXACT fields from your provided documentation
    # Target: Danaher (DHR)
    payload = {
        "ticker": "DHR_US_EQ",
        "quantity": 1.0,
        "extendedHours": True
    }
    
    # Official endpoint for market orders
    url = f"{base_url}/orders/market"
    
    print(f"📡 Sending Official Market Payload: {json.dumps(payload, indent=2)}")
    try:
        resp = requests.post(url, json=payload, auth=auth, timeout=15)
        print(f"📥 Response Code: {resp.status_code}")
        print(f"📄 Body: {resp.text}")

        final_msg = ""
        if resp.status_code == 200:
            final_msg = "✅ **DOC-COMPLIANT SUCCESS**\n\nMarket order for 1.0 DHR has been QUEUED successfully."
        else:
            final_msg = f"❌ **DOC-COMPLIANT FAILED**\n\nError: {resp.status_code}\nBody: `{resp.text}`"
            if "currency" in resp.text.lower():
                final_msg += "\n\n💡 *Confirmed: This US stock is blocked due to Main Account Currency (GBP) restrictions.*"

        # Telegram Report
        if token and chat_id:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                           data={"chat_id": chat_id, "text": final_msg, "parse_mode": "Markdown"})

    except Exception as e:
        print(f"❌ Exception: {e}")
