import json
import os
import shutil
import sys
from datetime import datetime

# Set stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

STATE_FILE = "live_state.json"
BACKUP_FILE = "live_state_backup.json"

def normalize_state():
    print("🛡️ Sovereign Guard: Initiating Global Normalization (Pence -> Pounds)...")
    
    if not os.path.exists(STATE_FILE):
        print(f"❌ Error: {STATE_FILE} not found.")
        return

    # 1. Backup
    shutil.copy(STATE_FILE, BACKUP_FILE)
    print(f"✅ Backup created: {BACKUP_FILE}")

    with open(STATE_FILE, 'r') as f:
        state = json.load(f)

    holdings = state.get('holdings', [])
    updated_holdings = []
    
    normalization_count = 0
    
    for h in holdings:
        ticker = h.get('Ticker', '')
        currency = h.get('Currency', '')
        price = h.get('Price', 0.0)
        
        # Heuristic: If it looks like a UK stock and price is huge (e.g. > 2000 for standard blue chips) 
        # normally traded in pence. 
        # OR explicitly if currency is GBX/GBp
        
        should_normalize = False
        
        # Explicit checks
        if currency in ['GBX', 'GBp']:
            should_normalize = True
            
        # Ticker suffix checks for UK
        elif ticker.endswith('l') or ticker.endswith('.L') or "_UK_EQ" in ticker:
             # Safety check: Don't normalize if it's already small (e.g. penny stock that is ACTUALLY pennies? 
             # No, standard is EVERYTHING is in pence on LSE in these feeds usually, but let's be careful).
             # If price > 100, assume it's pence.
             if price > 50: 
                 should_normalize = True

        if should_normalize:
            # Check if likely already normalized (e.g. Price is 50.20 vs 5020.0)
            # Rio Tinto ~5000p. If we see 5000, we divide. If we see 50, we leave it.
            if price > 200: # modest threshold (e.g. RR. is 400p+, LGEN is 200p+)
                 print(f"   🔧 Normalizing {ticker}: {price} -> {price/100.0}")
                 
                 h['Price'] = price / 100.0
                 h['Price_GBP'] = h.get('Price_GBP', price) / 100.0
                 h['Avg_Price'] = h.get('Avg_Price', 0) / 100.0
                 h['Value'] = h.get('Value', 0) / 100.0
                 h['Value_GBP'] = h.get('Value_GBP', 0) / 100.0
                 h['PL'] = h.get('PL', 0) / 100.0
                 h['PL_GBP'] = h.get('PL_GBP', 0) / 100.0
                 
                 normalization_count += 1
        
        updated_holdings.append(h)

    state['holdings'] = updated_holdings
    
    # Recalculate totals
    total_val = sum(h.get('Value_GBP', 0) for h in updated_holdings)
    print(f"💰 New Total Wealth (Assets Only): £{total_val:,.2f}")
    
    # Update state
    state['total_gbp'] = total_val
    # We might need to update account totals too if they were derived? 
    # Usually Account Summary from API is correct (GBP), it's just the positions that are raw.
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)
        
    print(f"✅ Normalization Complete. Fixed {normalization_count} assets.")
    print("🚀 Triggering Artist to render fixed dashboard...")
    os.system("python generate_static.py")

if __name__ == "__main__":
    normalize_state()
