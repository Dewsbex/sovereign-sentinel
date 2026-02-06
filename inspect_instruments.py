import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.21 - INSTRUMENT INSPECTOR
print("🚀 INSPECTING INSTRUMENTS...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    
    if not t212_key:
        print("❌ ERROR: T212_API_KEY is empty.")
        exit(1)

    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"

    # Search for Citigroup
    # We'll fetch the list of all instruments and filter for "Citigroup"
    print("📡 Fetching instrument list...")
    try:
        r = requests.get(f"{base_url}/instruments", auth=auth, timeout=30)
        if r.status_code == 200:
            instruments = r.json()
            matches = [inst for inst in instruments if "Citigroup" in inst.get('name', '') or " C " in inst.get('ticker', '') or inst.get('ticker') == 'C']
            
            print(f"✅ Found {len(matches)} matches:")
            for m in matches:
                print(f"🔹 Ticker: {m.get('ticker')} | Code: {m.get('id')} | Name: {m.get('name')}")
            
            # Also check a known good one like AAPL to verify format
            aapl = [inst for inst in instruments if inst.get('ticker') == 'AAPL']
            if aapl:
                print(f"🔹 Reference (AAPL): {aapl[0].get('id')}")
                
        else:
            print(f"❌ Failed to fetch instruments: {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
