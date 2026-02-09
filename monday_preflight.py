from trading212_client import Trading212Client
import datetime

client = Trading212Client()
cash = client.get_account_summary()
pos = client.get_open_positions()

report = [
    "*=== LIVE STATUS ===*",
    f"Free Cash: £{cash.get('free', 0):,.2f}",
    f"Portfolio P/L: £{cash.get('ppl', 0):,.2f}\n",
    "*=== TOP POSITIONS ===*"
]

if isinstance(pos, list):
    for p in pos[:10]:
        t = p.get('ticker') or p.get('instrument', {}).get('ticker', '???')
        t = t.replace('_US_EQ', '').replace('l_EQ', '')
        report.append(f"{t}: £{p.get('ppl', 0):>8.2f}")

client.send_telegram("\n".join(report))
