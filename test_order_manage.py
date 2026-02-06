import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.33 - ORDER MANAGEMENT MODULE (Fetch & Cancel)
print("🚀 STARTING ORDER MANAGEMENT TEST...")

def get_orders(base_url, auth):
    print("📡 Fetching all active orders...")
    resp = requests.get(f"{base_url}/orders", auth=auth, timeout=15)
    if resp.status_code == 200:
        orders = resp.json()
        print(f"✅ Found {len(orders)} active orders.")
        for o in orders:
            print(f"🔹 ID: {o.get('id')} | {o.get('ticker')} | {o.get('type')} | {o.get('status')}")
        return orders
    else:
        print(f"❌ Failed to fetch orders: {resp.status_code}")
        return []

def cancel_order(base_url, auth, order_id):
    print(f"📡 Attempting to cancel Order ID: {order_id}...")
    # T212 API uses DELETE /orders/{id}
    resp = requests.delete(f"{base_url}/orders/{order_id}", auth=auth, timeout=15)
    if resp.status_code == 200:
        print(f"✅ SUCCESS! Order {order_id} cancelled.")
        return True
    else:
        print(f"❌ Deletion failed: {resp.status_code} - {resp.text}")
        return False

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    # 1. Fetch current list
    orders = get_orders(base_url, auth)
    
    # 2. Logic to cancel the most recent one (if requested for test)
    # For now, this script just lists them so you can see your DHR tests.
    
    # Telegram Notification Logic
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    if token and chat_id:
        msg_lines = ["📡 **ACTIVE ORDERS REPORT**"]
        if orders:
            for o in orders:
                msg_lines.append(f"🆔 `{o.get('id')}` | {o.get('ticker')} | {o.get('type')}")
        else:
            msg_lines.append("✅ No active orders found.")
            
        final_msg = "\n".join(msg_lines)
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                       data={"chat_id": chat_id, "text": final_msg, "parse_mode": "Markdown"})

    if orders:
        print("\n💡 ACTION: To cancel an order, use: python test_order_manage.py --cancel ID")
