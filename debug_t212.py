import requests
import os
import base64
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET", "")
BASE_URL = "https://live.trading212.com/api/v0/equity"

def get_headers():
    if not API_KEY:
        raise ValueError("No API Key")
    if API_SECRET:
        creds = f"{API_KEY}:{API_SECRET}"
    else:
        creds = f"{API_KEY}:"
    encoded = base64.b64encode(creds.encode("utf-8")).decode("utf-8")
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json"
    }

def debug():
    headers = get_headers()
    print("Fetching one position for debug...")
    r = requests.get(f"{BASE_URL}/positions", headers=headers)
    if r.status_code == 200:
        pos = r.json()
        if pos:
            print("First position keys:", pos[0].keys())
            print("First position data:", pos[0])
        else:
            print("No positions found.")
    else:
        print(f"Error {r.status_code}: {r.text}")

if __name__ == "__main__":
    debug()
