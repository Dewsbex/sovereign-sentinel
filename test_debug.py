import os
import json
from datetime import datetime

# MOCK DATA
mock_portfolio = [
    {
        "ticker": "AAPL_US_EQ",
        "currency": "USD",
        "quantity": 10,
        "currentPrice": 220.50,
        "averagePrice": 150.00
    },
    {
        "ticker": "RR.L", # UK Stock
        "currency": "GBX",
        "quantity": 1000,
        "currentPrice": 450.00, # Pence
        "averagePrice": 300.00 # Pence
    }
]

instrument_map = {
    "AAPL_US_EQ": {"symbol": "AAPL", "currency": "USD"},
    "RR.L": {"symbol": "RR", "currency": "GBX"}
}

def clean_ticker(ticker_raw):
    t = ticker_raw.replace('l_EQ', '').replace('_EQ', '').replace('.L', '')
    return t

def safe_float(value, default=0.0):
    if value is None: return default
    try:
        clean = str(value).replace(',', '').replace('$', '').replace('£', '')
        return float(clean)
    except ValueError:
        return default

def test_logic():
    print("Testing Logic...")
    
    cash_reserves = 1000.0
    portfolio_raw = mock_portfolio
    
    # --- LOGIC UNDER TEST ---
    heatmap_data = []
    
    for pos in portfolio_raw:
        raw_ticker = pos.get('ticker')
        if not raw_ticker: continue

        meta = instrument_map.get(raw_ticker, {})
        ticker = meta.get('symbol') or clean_ticker(raw_ticker)
        
        currency = meta.get('currency') or pos.get('currency', '')
        current_price = safe_float(pos.get('currentPrice', 0))
        avg_price = safe_float(pos.get('averagePrice', 0))
        qty = safe_float(pos.get('quantity', 0))
        
        is_pence = False
        if currency in ['GBX', 'GBp'] or (current_price > 1000 and currency == 'GBP'):
             is_pence = True
        
        if is_pence:
            current_price /= 100.0
            avg_price /= 100.0

        market_val = qty * current_price
        invested = qty * avg_price
        if invested > 0:
            pnl_cash = market_val - invested
            pnl_pct = ((market_val - invested) / invested) * 100
        else:
            pnl_cash = 0.0
            pnl_pct = 0.0

        val_str = f"£{market_val:,.2f}"
        sign = "+" if pnl_cash >= 0 else "-"
        pnl_str = f"{sign}£{abs(pnl_cash):,.2f} ({sign}{abs(pnl_pct):.2f}%)"

        heatmap_data.append({
            'x': ticker,
            'y': market_val,
            'fillColor': '#28a745' if pnl_cash >= 0 else '#dc3545',
            'custom_main': val_str,
            'custom_sub': pnl_str
        })
        
    print(f"Heatmap Data: {json.dumps(heatmap_data, indent=2)}")
    
    heatmap_data = sorted(heatmap_data, key=lambda k: k['y'], reverse=True)
    total_holdings_val = sum(d['y'] for d in heatmap_data)
    total_wealth = cash_reserves + total_holdings_val
    
    print(f"Total Wealth: {total_wealth}")
    print("Logic Test Output: SUCCESS")

if __name__ == "__main__":
    test_logic()
