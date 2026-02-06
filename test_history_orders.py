import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.38 - ORDER HISTORY MODULE
print("🚀 TESTING ORDER HISTORY...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    print("📡 Fetching historical orders...")
    # Get last 50 orders
    resp = requests.get(f"{base_url}/history/orders?limit=50", auth=auth, timeout=15)
    
    print(f"📥 Response Code: {resp.status_code}")
    if resp.status_code == 200:
        # DEBUG
        if orders:
            print(f"🔎 DEBUG Raw Item: {orders[0]}")

        msg_lines = ["📜 **ORDER HISTORY REPORT**"]
        for o in orders:
            if isinstance(o, dict):
                info = f"{o.get('dateCreated')} | {o.get('ticker')} | {o.get('status')} | {o.get('filledQuantity')} @ {o.get('fillPrice')}"
                print(f"   📜 {info}")
                msg_lines.append(f"📜 {info}")
            else:
                print(f"   ⚠️ Raw: {o}")
                msg_lines.append(f"⚠️ Raw: {o}")

        # Telegram Notification
        token = os.getenv('TELEGRAM_TOKEN', '').strip()
        chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
        if token and chat_id:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                           data={"chat_id": chat_id, "text": "\n".join(msg_lines), "parse_mode": "Markdown"})
