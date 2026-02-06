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
        divs = resp.json()
        print(f"✅ Found {len(divs)} dividend records.")
        for d in divs:
            print(f"   💵 {d.get('ticker')} | {d.get('amount')} {d.get('currency')} | {d.get('paidOn')}")
    else:
        print(f"❌ Failed to fetch dividends: {resp.text}")
