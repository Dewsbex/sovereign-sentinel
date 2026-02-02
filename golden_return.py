import requests
import json
import os
import csv
import io
import time
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("T212_API_KEY")
api_secret = os.environ.get("T212_API_SECRET")
auth = HTTPBasicAuth(api_key, api_secret)

def get_report():
    for _ in range(5):
        r = requests.get('https://live.trading212.com/api/v0/equity/history/exports', auth=auth)
        if r.status_code == 200:
            reports = r.json()
            finished = [rep for rep in reports if rep.get('status') == 'Finished' and rep.get('downloadLink')]
            if finished: return finished[0]['downloadLink']
        elif r.status_code == 429:
            print("429, waiting...")
            time.sleep(5)
        else:
            print(f"Error {r.status_code}")
            return None
    return None

url = get_report()
if not url:
    print("Could not get report.")
    exit()

r_dl = requests.get(url)
reader = csv.DictReader(io.StringIO(r_dl.text))

# Metrics to track
realized_trades = 0.0 # Sell - Buy
dividends = 0.0
interest = 0.0
fees_taxes = 0.0
other = 0.0

actions_seen = {}

for row in reader:
    action = row.get('Action')
    total = row.get('Total')
    if not action or not total: continue
    
    try:
        val = float(str(total).replace('£','').replace('$','').replace(',',''))
    except:
        continue
    
    actions_seen[action] = actions_seen.get(action, 0) + 1
    
    # Logic for Performance:
    # Market buy, Limit buy -> Negative (Cost)
    # Market sell, Limit sell -> Positive (Revenue)
    # Dividend, Interest -> Positive (Income)
    # Fee, Tax, Stamp duty -> Negative (Cost)
    
    if 'buy' in action.lower():
        realized_trades -= val # Cash OUT
    elif 'sell' in action.lower():
        realized_trades += val # Cash IN
    elif 'dividend' in action.lower():
        dividends += val
    elif 'interest' in action.lower():
        interest += val
    elif any(x in action.lower() for x in ['fee', 'tax', 'stamp duty']):
        fees_taxes -= val
    elif 'deposit' in action.lower() or 'withdrawal' in action.lower():
        pass # Ignore for performance
    else:
        other += val
        print(f"Unknown action: {action} val: {val}")

print("\n--- PERFORMANCE COMPONENTS ---")
print(f"Net Trade Balance (Sell - Buy):  £{realized_trades:,.2f}")
print(f"Total Dividends:                 £{dividends:,.2f}")
print(f"Total Interest on Cash:          £{interest:,.2f}")
print(f"Total Fees & Taxes:             -£{abs(fees_taxes):,.2f}")
print(f"Other (Referrals, etc):          £{other:,.2f}")

# Note: The calculation above is "Net Cash Flow from Activities".
# To get Total Return, we need:
# Total Return = (Current Portfolio Value - Net Trade Balance) + Dividends + Interest ...
# Wait, actually:
# Total Return = (Current Value of Held Shares - Cost of Held Shares) + Realized Profit + Dividends + Interest ...

# If we have the full history, (Sells - Buys) is the "Net Cash flow into/out of positions"
# But we need to know the CURRENT value.
# Account Value = Net Deposits + Total Return
# Total Return = Account Value - Net Deposits

# Let's find Net Deposits
net_deposits = 0.0
reader2 = csv.DictReader(io.StringIO(r_dl.text)) # Reset reader
for row in reader2:
    action = row.get('Action')
    total = row.get('Total')
    if not action or not total: continue
    try:
        val = float(str(total).replace('£','').replace('$','').replace(',',''))
    except: continue
    
    if action == 'Deposit':
        net_deposits += val
    elif action == 'Withdrawal':
        net_deposits -= val

r_sum = requests.get('https://live.trading212.com/api/v0/equity/account/summary', auth=auth)
summary = r_sum.json()
account_value = summary.get('totalValue', 0.0)

total_return = account_value - net_deposits

print("\n--- THE GOLDEN FORMULA ---")
print(f"Current Account Value:   £{account_value:,.2f}")
print(f"Net Deposits (History):  £{net_deposits:,.2f}")
print(f"Calculated Total Return: £{total_return:,.2f}")
print(f"App Display Target:      £24,871.91")
print(f"Variance:                £{total_return - 24871.91:,.2f}")
