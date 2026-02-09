#!/usr/bin/env python3
"""Quick test of Trading212 connection and account status"""

from trading212_client import Trading212Client

try:
    print("Testing Trading 212 connection...")
    client = Trading212Client()
    
    account = client.get_account_info()
    print(f"\n✅ CONNECTION SUCCESSFUL!")
    print(f"{'='*50}")
    print(f"Account ID: {account.get('id')}")
    print(f"Currency: {account.get('currency')}")
    print(f"Total Value: £{account.get('totalValue', 0):,.2f}")
    print(f"Cash Available: £{account['cash'].get('availableToTrade', 0):,.2f}")
    print(f"In Pies: £{account['cash'].get('inPies', 0):,.2f}")
    print(f"Reserved: £{account['cash'].get('reservedForOrders', 0):,.2f}")
    print(f"{'='*50}")
    
    positions = client.get_positions()
    print(f"Open Positions: {len(positions)}")
    
    if positions:
        print(f"\nTop 3 positions:")
        for pos in positions[:3]:
            print(f"  {pos['ticker']}: {pos.get('quantity', 0)} shares")
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED")
    print(f"Error: {e}")
