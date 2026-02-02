import json
with open('live_state.json', 'r') as f:
    state = json.load(f)
    acc = state.get('account', {})
    inv = acc.get('investments', {})
    
    realized = inv.get('realizedProfitLoss', 0)
    unrealized = inv.get('unrealizedProfitLoss', 0)
    
    print(f"Realized P/L from API: £{realized:,.2f}")
    print(f"Unrealized P/L from API: £{unrealized:,.2f}")
    print(f"Sum (no dividends): £{realized + unrealized:,.2f}")
    
    # Check dividends
    try:
        with open('data/ledger_cache.json', 'r') as lf:
            ledger = json.load(lf)
            assets = ledger.get('assets', {})
            total_div = sum(a.get('dividends', 0) for a in assets.values())
            print(f"\nTotal Dividends from Ledger: £{total_div:,.2f}")
            print(f"Calculated Total Return: £{realized + unrealized + total_div:,.2f}")
    except:
        print("No ledger cache found")
    
    print(f"\nTarget Total Return: £25,000.00")
    print(f"Difference: £{25000 - (realized + unrealized):,.2f}")
