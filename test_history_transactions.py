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
        txs = resp.json()
        print(f"✅ Found {len(txs)} transactions.")
        for t in txs:
            print(f"   🏦 {t.get('date')} | {t.get('type')} | {t.get('amount')} {t.get('currency')}")
    else:
        print(f"❌ Failed to fetch transactions: {resp.text}")
