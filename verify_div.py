import json
with open('data/ledger_cache.json', 'r') as f:
    data = json.load(f)
    assets = data.get('assets', {})
    total_div = sum(a.get('dividends', 0) for a in assets.values())
    print(f"Total Dividends from Ledger Cache: {total_div}")
