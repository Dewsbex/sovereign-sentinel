import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("T212_API_KEY", "").strip()
BASE_URL = "https://live.trading212.com/api/v0/"

print(f"Testing Key: {API_KEY[:5]}...{API_KEY[-5:]} (Len: {len(API_KEY)})")

endpoints = [
    "equity/portfolio",
    "equity/account/info",
    "equity/account/cash",
]

for ep in endpoints:
    url = f"{BASE_URL}{ep}"
    print(f"\n--- Testing Endpoint: {ep} ---")
    
    # Try Direct
    try:
        r = requests.get(url, headers={"Authorization": API_KEY})
        print(f"Direct   : {r.status_code}")
    except: pass
    
    # Try Bearer
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
        print(f"Bearer   : {r.status_code}")
    except: pass
