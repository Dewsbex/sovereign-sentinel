import requests
import json
import os
import csv
import io
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("T212_API_KEY")
api_secret = os.environ.get("T212_API_SECRET")
auth = HTTPBasicAuth(api_key, api_secret)

r = requests.get('https://live.trading212.com/api/v0/equity/history/exports', auth=auth)
if r.status_code != 200:
    print(f"Error: {r.status_code}")
    exit()

reports = r.json()
finished = [rep for rep in reports if rep.get('status') == 'Finished' and rep.get('downloadLink')]

if not finished:
    print("No finished reports found.")
    exit()

# Try to download the most recent one
url = finished[0]['downloadLink']
print(f"Downloading from: {url[:100]}...")

r_dl = requests.get(url)
if r_dl.status_code != 200:
    print(f"Download error: {r_dl.status_code}")
    exit()

reader = csv.DictReader(io.StringIO(r_dl.text))
action_totals = {}

for row in reader:
    action = row.get('Action')
    total = row.get('Total')
    if not action or not total: continue
    
    try:
        # T212 CSV uses commas or other formatting sometimes
        val_str = str(total).replace('£','').replace('$','').replace(',','')
        amt = float(val_str)
    except:
        continue
        
    if action not in action_totals:
        action_totals[action] = 0.0
    action_totals[action] += amt

print("\n--- RESULTS ---")
for action, total in sorted(action_totals.items(), key=lambda x: x[1], reverse=True):
    print(f"{action:30}: £{total:,.2f}")

# Calculate Performance Components
# We want to exclude DEPOSITS and WITHDRAWALS
ignored = ['Deposit', 'Withdrawal']
performance_actions = {k:v for k,v in action_totals.items() if not any(i in k for i in ignored)}

total_perf = sum(performance_actions.values())
print(f"\nTotal Performance (excluding deposits/withdrawals): £{total_perf:,.2f}")
