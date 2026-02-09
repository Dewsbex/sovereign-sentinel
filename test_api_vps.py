from trading212_client import Trading212Client
import json
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = Trading212Client()
    
    print("--- ACCOUNT SUMMARY ---")
    summary = client.get_account_info()
    print(json.dumps(summary, indent=2))
    
    print("\n--- FIRST POSITION ---")
    positions = client.get_positions()
    if positions and isinstance(positions, list):
        print(json.dumps(positions[0], indent=2))
    else:
        print("No positions found or error:", positions)

except Exception as e:
    print(f"ERROR: {e}")
