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
        print(f"✅ Found {len(positions)} open positions.")
        
        total_ppl = 0.0
        for p in positions:
            ticker = p.get('ticker')
            qty = p.get('quantity')
            ppl = p.get('ppl', 0) # Profit/Loss
            total_ppl += float(ppl) if ppl else 0.0
            print(f"   🔹 {ticker}: {qty} shares | P/L: {ppl}")
            
        print(f"\n💰 Total Unrealiased P/L: {total_ppl:.2f}")
    else:
        print(f"❌ Failed to fetch positions: {resp.text}")
