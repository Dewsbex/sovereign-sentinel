import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("T212_API_KEY", "").strip()
BASE_URL = "https://live.trading212.com/api/v0/"

url = f"{BASE_URL}equity/metadata/exchanges"
r = requests.get(url, headers={"Authorization": API_KEY})
print(f"Exchanges: {r.status_code}")
