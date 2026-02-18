
import os
from dotenv import load_dotenv
import requests

def check_auth():
    load_dotenv()
    key = os.getenv('TRADING212_API_KEY')
    if not key:
        print("❌ TRADING212_API_KEY not found in .env")
        return
    
    print(f"✅ Key Found: {key[:5]}...{key[-5:]}")
    
    url = "https://live.trading212.com/api/v0/equity/account/cash"
    headers = {"Authorization": key}
    
    try:
        res = requests.get(url, headers=headers)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_auth()
