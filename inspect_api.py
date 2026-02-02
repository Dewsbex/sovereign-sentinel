import requests, os, json
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET")
BASE_URL = "https://live.trading212.com/api/v0/equity"
auth = HTTPBasicAuth(API_KEY, API_SECRET)

r = requests.get(f"{BASE_URL}/account/summary", auth=auth)
if r.status_code == 200:
    with open('debug_summary.json', 'w') as f:
        json.dump(r.json(), f, indent=4)
    print("Dumped summary to debug_summary.json")
