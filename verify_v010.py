import json
import os

with open('live_state.json', 'r') as f:
    state = json.load(f)

# The generate_static.py calculates it on the fly, so we need to run that logic
account = state['account']
invest_data = account['investments']
realized_pl = invest_data['realizedProfitLoss']
unrealized_pl = invest_data['unrealizedProfitLoss']

total_dividends = 0.0
total_interest = 0.0
total_fees = 0.0

cache_path = "data/ledger_cache.json"
if os.path.exists(cache_path):
    with open(cache_path, 'r') as f:
        ledger = json.load(f)
        assets = ledger.get('assets', {})
        total_dividends = sum(a.get('dividends', 0) for a in assets.values())
        globs = ledger.get('global', {})
        total_interest = globs.get('interest', 0.0)
        total_fees = globs.get('fees_taxes', 0.0)

total_return = realized_pl + unrealized_pl + total_dividends + total_interest + total_fees
print(f"--- DETAILED BREAKDOWN ---")
print(f"Realized P/L:   £{realized_pl:,.2f}")
print(f"Unrealized P/L: £{unrealized_pl:,.2f}")
print(f"Dividends:      £{total_dividends:,.2f}")
print(f"Interest:       £{total_interest:,.2f}")
print(f"Fees/Taxes:    -£{abs(total_fees):,.2f}")
print(f"--------------------------")
print(f"Total Return:   £{total_return:,.2f}")
print(f"Target (App):   £24,871.91")
print(f"Difference:     £{total_return - 24871.91:,.2f}")
