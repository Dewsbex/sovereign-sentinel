import json

with open('t212_api_dump.json', 'r') as f:
    data = json.load(f)

summary = data['summary']
positions = data['positions']

print("=" * 80)
print("ANALYSIS: Total Return Discrepancy")
print("=" * 80)

# From summary
realized = summary['investments']['realizedProfitLoss']
unrealized_summary = summary['investments']['unrealizedProfitLoss']
total_return_calculated = realized + unrealized_summary

print(f"\n[FROM ACCOUNT SUMMARY]")
print(f"Realized P/L: £{realized:,.2f}")
print(f"Unrealized P/L: £{unrealized_summary:,.2f}")
print(f"Calculated Total Return: £{total_return_calculated:,.2f}")

# Sum unrealized from positions
unrealized_from_positions = sum(p['walletImpact']['unrealizedProfitLoss'] for p in positions)
print(f"\n[FROM POSITIONS]")
print(f"Sum of Unrealized P/L: £{unrealized_from_positions:,.2f}")
print(f"Match with Summary? {abs(unrealized_summary - unrealized_from_positions) < 0.01}")

# Trading 212 App shows
app_total_return = 24871.91
print(f"\n[TRADING 212 APP]")
print(f"Displayed Total Return: £{app_total_return:,.2f}")

print(f"\n[DISCREPANCY ANALYSIS]")
discrepancy = app_total_return - total_return_calculated
print(f"Difference: £{discrepancy:,.2f}")
print(f"Percentage: {(discrepancy / app_total_return) * 100:.2f}%")

# Could it be that we need to check totalValue?
total_value = summary['totalValue']
cash = summary['cash']['availableToTrade'] + summary['cash']['reservedForOrders']
investments_value = total_value - cash

print(f"\n[VALUE RECONCILIATION]")
print(f"Total Account Value: £{total_value:,.2f}")
print(f"Total Cash: £{cash:,.2f}")
print(f"Investment Value (Total - Cash): £{investments_value:,.2f}")
print(f"Investment Value from API: £{summary['investments']['currentValue']:,.2f}")
print(f"Match? {abs(investments_value - summary['investments']['currentValue']) < 1.0}")

# Try reverse engineering the app's calculation
# If app shows 24,871.91 and we have:
# Maybe the app is using a different time period or including closed positions?
print(f"\n[HYPOTHESIS: MISSING COMPONENT]")
print(f"Missing amount: £{discrepancy:,.2f}")
print(f"This represents {(discrepancy / realized) * 100:.2f}% of realized P/L")
print(f"\nPossible explanations:")
print(f"1. Closed positions from earlier time period")
print(f"2. Interest earned (£{discrepancy:,.2f})")
print(f"3. Fee adjustments or rebates")
print(f"4. Dividend timing differences")
print(f"5. API lag - app showing more recent data")
