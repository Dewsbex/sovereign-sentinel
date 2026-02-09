from trading212_client import Trading212Client
import json

try:
    client = Trading212Client()
    print("Headers:", client.headers)
    
    summary = client.get_account_info()
    print("Account Summary Result:")
    print(json.dumps(summary, indent=2))
    
    positions = client.get_positions()
    print("\nPositions Result (First 2):")
    if isinstance(positions, list):
        print(json.dumps(positions[:2], indent=2))
    else:
        print(json.dumps(positions, indent=2))
        
    cash = client.get_account_summary()
    print("\nCash Result:")
    print(json.dumps(cash, indent=2))

except Exception as e:
    print(f"ERROR: {e}")
