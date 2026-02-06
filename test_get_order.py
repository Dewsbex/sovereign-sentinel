import os
import requests
import json
import sys
from requests.auth import HTTPBasicAuth

# V32.35 - GET ORDER BY ID MODULE
print("🚀 TESTING GET ORDER BY ID...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    order_id = None
    
    # Check if ID passed as argument
    if len(sys.argv) > 1:
        order_id = sys.argv[1]
    else:
        # Auto-discovery: Get the most recent active order
        print("hint: You can pass an ID as an argument: python test_get_order.py <ID>")
        print("📡 Fetching active orders to find a candidate...")
        r = requests.get(f"{base_url}/orders", auth=auth, timeout=15)
        if r.status_code == 200:
            orders = r.json()
            if orders:
                order_id = orders[0].get('id')
                print(f"✅ Found candidate ID: {order_id}")
            else:
                print("⚠️ No active orders found to test with.")
        else:
            print(f"❌ Failed to list orders: {r.status_code}")

    if order_id:
        print(f"📡 Requesting details for Order ID: {order_id}...")
        resp = requests.get(f"{base_url}/orders/{order_id}", auth=auth, timeout=15)
        
        token = os.getenv('TELEGRAM_TOKEN', '').strip()
        chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
        
        print(f"📥 Response Code: {resp.status_code}")
        body_text = json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text
        print(f"📄 Body: {body_text}")
        
        msg = ""
        if resp.status_code == 200:
            print("✅ GET ORDER SUCCESS")
            msg = f"✅ **GET ORDER REPORT**\n\n`{body_text}`"
        else:
            print("❌ GET ORDER FAILED")
            msg = f"❌ **GET ORDER FAILED**\n\nError: {resp.status_code}\n`{body_text}`"

        if token and chat_id:
             requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                           data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
