
import os
import sys
import json
from trading212_client import Trading212Client

# Helper to serialise
def default(o):
    return str(o)

print("--- DEBUGGING T212 API ON VPS ---")
client = Trading212Client()
print(f"API Key present: {bool(client.api_key)}")
print(f"Base URL: {client.base_url}")

print("\n--- FETCHING ACCOUNT ---")
try:
    cash = client.get_account_summary()
    print(json.dumps(cash, indent=2, default=default))
except Exception as e:
    print(f"Error fetching cash: {e}")

print("\n--- FETCHING POSITIONS ---")
try:
    positions = client.get_positions()
    print(f"Type: {type(positions)}")
    if isinstance(positions, list):
        print(f"Count: {len(positions)}")
        if len(positions) > 0:
            print("First Position Sample:")
            print(json.dumps(positions[0], indent=2, default=default))
    else:
        print("Raw Response:")
        print(json.dumps(positions, indent=2, default=default))
except Exception as e:
    print(f"Error fetching positions: {e}")
