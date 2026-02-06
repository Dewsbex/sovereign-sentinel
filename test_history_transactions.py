import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.39 - TRANSACTION HISTORY MODULE
print("🚀 TESTING TRANSACTION HISTORY...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    print("📡 Fetching transactions...")
    # Get last 50 transactions
    resp = requests.get(f"{base_url}/history/transactions?limit=50", auth=auth, timeout=15)
    
    print(f"📥 Response Code: {resp.status_code}")
    if resp.status_code == 200:
        if txs:
            print(f"🔎 DEBUG Raw Item: {txs[0]}")
            
        msg_lines = ["🏦 **TRANSACTION REPORT**"]
        for t in txs:
            if isinstance(t, dict):
                info = f"{t.get('date')} | {t.get('type')} | {t.get('amount')} {t.get('currency')}"
                print(f"   🏦 {info}")
                msg_lines.append(f"🏦 {info}")
            else:
                print(f"   ⚠️ Raw: {t}")
                msg_lines.append(f"⚠️ Raw: {t}")

        # Telegram Notification
        token = os.getenv('TELEGRAM_TOKEN', '').strip()
        chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
        if token and chat_id:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                           data={"chat_id": chat_id, "text": "\n".join(msg_lines), "parse_mode": "Markdown"})
