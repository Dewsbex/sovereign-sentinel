import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("T212_API_KEY", "").strip()
URL = "https://live.trading212.com/api/v0/equity/portfolio"

print(f"Testing Basic Auth with Key Only...")

# Try Basic Auth (Key as Username, Empty Password)
auth_str = f"{API_KEY}:"
encoded = base64.b64encode(auth_str.encode()).decode()
headers = {"Authorization": f"Basic {encoded}"}

r = requests.get(URL, headers=headers)
print(f"Basic Auth (Key:): {r.status_code}")

# Try Basic Auth (Key as Password, Empty Username)
auth_str = f":{API_KEY}"
encoded = base64.b64encode(auth_str.encode()).decode()
headers = {"Authorization": f"Basic {encoded}"}

r = requests.get(URL, headers=headers)
print(f"Basic Auth (:Key): {r.status_code}")
