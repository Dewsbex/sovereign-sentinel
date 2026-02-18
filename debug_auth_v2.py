
import os
import base64
import requests
from dotenv import load_dotenv

def diagnose_auth():
    load_dotenv()
    key = os.getenv('TRADING212_API_KEY')
    secret = os.getenv('TRADING212_API_SECRET')
    
    print(f"Key Present: {bool(key)}")
    print(f"Secret Present: {bool(secret)}")
    
    url = "https://live.trading212.com/api/v0/equity/account/cash"
    
    # Method 1: API Key Header
    if key:
        print("\n--- Method 1: Standard API Key Header ---")
        headers = {"Authorization": key}
        try:
            res = requests.get(url, headers=headers)
            print(f"Status: {res.status_code}")
            if res.status_code == 200:
                print("✅ SUCCESS")
            else:
                print(f"❌ FAILED: {res.text[:100]}")
        except Exception as e:
            print(f"Error: {e}")

    # Method 2: Basic Auth
    if key and secret:
        print("\n--- Method 2: Basic Auth (Key:Secret) ---")
        auth_str = f"{key}:{secret}"
        auth_bytes = auth_str.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')
        headers = {"Authorization": f"Basic {base64_auth}"}
        try:
            res = requests.get(url, headers=headers)
            print(f"Basic Auth Status: {res.status_code}")
            if res.status_code == 200:
                print("✅ SUCCESS")
            else:
                print(f"❌ FAILED: {res.text[:100]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    diagnose_auth()
