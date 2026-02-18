
import os
import sys
import json
from trading212_client import Trading212Client

def default(o): return str(o)

print("--- DEBUG FULL POSITION OBJECT ---")
client = Trading212Client()

try:
    positions = client.get_positions()
    if isinstance(positions, list) and len(positions) > 0:
        # Print first 2 positions to see different currencies if possible
        for i, pos in enumerate(positions[:3]):
            print(f"\n--- POSITION {i+1} ({pos.get('ticker')}) ---")
            print(json.dumps(pos, indent=2, default=default))
    else:
        print("No positions or error:", positions)
except Exception as e:
    print(f"Error: {e}")
