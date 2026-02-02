"""
Complete Trading 212 API Inspector
Dumps all fields from account summary and positions to identify missing data
"""
import requests
import json
import os
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET")
BASE_URL = "https://live.trading212.com/api/v0/equity"
auth = HTTPBasicAuth(API_KEY, API_SECRET)

print("=" * 80)
print("TRADING 212 API COMPLETE INSPECTION")
print("=" * 80)

# 1. Account Summary
print("\n[1] ACCOUNT SUMMARY")
print("-" * 80)
r = requests.get(f"{BASE_URL}/account/summary", auth=auth)
if r.status_code == 200:
    summary = r.json()
    print(json.dumps(summary, indent=2))
    
    # Extract key fields
    print("\n[KEY FIELDS EXTRACTED]")
    print(f"Total Value: £{summary.get('totalValue', 0):,.2f}")
    
    cash = summary.get('cash', {})
    print(f"Cash Available: £{cash.get('availableToTrade', 0):,.2f}")
    print(f"Cash Reserved: £{cash.get('reservedForOrders', 0):,.2f}")
    
    inv = summary.get('investments', {})
    print(f"Current Investment Value: £{inv.get('currentValue', 0):,.2f}")
    print(f"Total Cost: £{inv.get('totalCost', 0):,.2f}")
    print(f"Realized P/L: £{inv.get('realizedProfitLoss', 0):,.2f}")
    print(f"Unrealized P/L: £{inv.get('unrealizedProfitLoss', 0):,.2f}")
    
    # Calculate
    realized = inv.get('realizedProfitLoss', 0)
    unrealized = inv.get('unrealizedProfitLoss', 0)
    calculated_return = realized + unrealized
    
    print(f"\n[CALCULATED TOTAL RETURN]")
    print(f"Realized + Unrealized = £{calculated_return:,.2f}")
    
    print(f"\n[TRADING 212 APP DISPLAYS]")
    print(f"Total Return: £24,871.91")
    print(f"Discrepancy: £{24871.91 - calculated_return:,.2f}")
    
else:
    print(f"ERROR: {r.status_code} - {r.text}")

# 2. Check for other endpoints or fields
print("\n" + "=" * 80)
print("[2] POSITIONS - CHECKING FOR ADDITIONAL P/L FIELDS")
print("-" * 80)

r = requests.get(f"{BASE_URL}/positions", auth=auth)
if r.status_code == 200:
    positions = r.json()
    
    total_unrealized_from_positions = 0
    
    for pos in positions[:3]:  # Show first 3 in detail
        print(f"\nPosition: {pos.get('instrument', {}).get('ticker', 'UNKNOWN')}")
        print(json.dumps(pos, indent=2))
        
        # Extract P/L
        wi = pos.get('walletImpact', {})
        total_unrealized_from_positions += wi.get('unrealizedProfitLoss', 0)
    
    # Sum all positions
    total_unrealized_sum = sum(p.get('walletImpact', {}).get('unrealizedProfitLoss', 0) for p in positions)
    print(f"\n[SUM OF ALL POSITION UNREALIZED P/L]")
    print(f"Total: £{total_unrealized_sum:,.2f}")
    
    print(f"\n[COMPARISON]")
    print(f"Account Summary Unrealized P/L: £{inv.get('unrealizedProfitLoss', 0):,.2f}")
    print(f"Sum of Position Unrealized P/L: £{total_unrealized_sum:,.2f}")
    print(f"Match: {abs(inv.get('unrealizedProfitLoss', 0) - total_unrealized_sum) < 0.01}")
    
else:
    print(f"ERROR: {r.status_code} - {r.text}")

# 3. Save for inspection
with open('t212_api_dump.json', 'w') as f:
    json.dump({
        'summary': summary if r.status_code == 200 else None,
        'positions': positions if r.status_code == 200 else None
    }, f, indent=2)
    
print("\n" + "=" * 80)
print("Full API response saved to: t212_api_dump.json")
print("=" * 80)
