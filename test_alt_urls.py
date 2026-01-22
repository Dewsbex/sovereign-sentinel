import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("T212_API_KEY", "").strip()

urls = [
    "https://api.trading212.com/api/v0/equity/portfolio",
    "https://api.trading212.com/v0/equity/portfolio",
    "https://live.trading212.com/api/v0/equity/portfolio",
]

for url in urls:
    try:
        r = requests.get(url, headers={"Authorization": API_KEY})
        print(f"{url}: {r.status_code}")
    except:
        print(f"{url}: Connection Error")
