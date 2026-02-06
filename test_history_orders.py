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
        orders = resp.json()
        print(f"✅ Found {len(orders)} historical orders.")
        for o in orders:
            # Display crucial execution info
            print(f"   📜 {o.get('dateCreated')} | {o.get('ticker')} | {o.get('status')} | {o.get('filledQuantity')} @ {o.get('fillPrice')}")
    else:
        print(f"❌ Failed to fetch order history: {resp.text}")
