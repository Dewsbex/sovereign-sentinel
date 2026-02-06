import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.37 - DIVIDEND HISTORY MODULE
print("🚀 TESTING DIVIDEND HISTORY...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    print("📡 Fetching paid out dividends...")
    # Get last 50 dividends
    resp = requests.get(f"{base_url}/history/dividends?limit=50", auth=auth, timeout=15)
    
    print(f"📥 Response Code: {resp.status_code}")
    if resp.status_code == 200:
        # DEBUG: Print raw first item to understand structure
        if divs:
            print(f"🔎 DEBUG Raw Item: {divs[0]}")
        
        msg_lines = ["💰 **DIVIDEND REPORT**"]
        for d in divs:
            # Handle potential string vs dict response
            if isinstance(d, dict):
                info = f"{d.get('ticker')} | {d.get('amount')} {d.get('currency')} | {d.get('paidOn')}"
                print(f"   💵 {info}")
                msg_lines.append(f"💵 {info}")
            else:
                print(f"   ⚠️ Unexpected item format: {d}")
                msg_lines.append(f"⚠️ Raw: {d}")

        # Telegram Notification
        token = os.getenv('TELEGRAM_TOKEN', '').strip()
        chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
        if token and chat_id:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                           data={"chat_id": chat_id, "text": "\n".join(msg_lines), "parse_mode": "Markdown"})
