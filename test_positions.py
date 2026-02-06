import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.36 - POSITIONS MODULE
print("🚀 TESTING POSITIONS MODULE...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    print("📡 Fetching open positions...")
    resp = requests.get(f"{base_url}/positions", auth=auth, timeout=15)
    
    print(f"📥 Response Code: {resp.status_code}")
    if resp.status_code == 200:
        positions = resp.json()
        # DEBUG
        if positions:
            print(f"🔎 DEBUG Raw Item: {positions[0]}")
            
        msg_lines = ["📊 **POSITIONS REPORT**"]
        total_ppl = 0.0
        
        for p in positions:
            if isinstance(p, dict):
                ticker = p.get('ticker')
                qty = p.get('quantity')
                # Spec: 'ppl' might not exist. Use walletImpact.unrealizedProfitLoss
                ppl = p.get('ppl') or p.get('walletImpact', {}).get('unrealizedProfitLoss', 0)
                total_ppl += float(ppl) if ppl else 0.0
                
                info = f"{ticker}: {qty} shares | P/L: {ppl}"
                print(f"   🔹 {info}")
                msg_lines.append(f"🔹 {info}")
            else:
                print(f"   ⚠️ Raw: {p}")
                msg_lines.append(f"⚠️ Raw: {p}")

        print(f"\n💰 Total Unrealiased P/L: {total_ppl:.2f}")
        msg_lines.append(f"\n💰 **Total P/L**: {total_ppl:.2f}")

        # Telegram Notification
        token = os.getenv('TELEGRAM_TOKEN', '').strip()
        chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
        if token and chat_id:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                           data={"chat_id": chat_id, "text": "\n".join(msg_lines), "parse_mode": "Markdown"})
