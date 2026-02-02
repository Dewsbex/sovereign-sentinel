import csv
import json
import os

CACHE_FILE = "data/ledger_cache.json"
CSV_FILE = "current_ledger.csv"

def run_injection():
    if not os.path.exists(CSV_FILE):
        print("CSV missing")
        return

    global_data = {
        'interest': 0.0,
        'fees_taxes': 0.0,
        'other_income': 0.0
    }
    
    with open(CSV_FILE, 'r', encoding='utf-16') as f:
        reader = csv.DictReader(f)
        for row in reader:
            action = row.get('Action')
            total_val = row.get('Total')
            if not action: continue
            
            try:
                amt = float(str(total_val).replace('£','').replace('$','').replace(',',''))
            except:
                amt = 0.0
                
            # Column-based fees
            fee_cols = ['Transaction fee', 'Dividend tax', 'Withholding tax', 'Currency conversion fee']
            for col in fee_cols:
                v = row.get(col)
                if v:
                    try:
                        fv = float(str(v).replace('£','').replace('$','').replace(',',''))
                        global_data['fees_taxes'] -= abs(fv)
                    except: pass
            
            # Action-based
            if 'interest' in action.lower():
                global_data['interest'] += amt
            elif not row.get('Ticker') and 'bonus' in action.lower():
                global_data['other_income'] += amt

    # Load and Update Cache
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        
        cache['global'] = global_data
        
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
        
        print(f"Injected Interest: £{global_data['interest']:,.2f}")
        print(f"Injected Fees:     £{global_data['fees_taxes']:,.2f}")
    else:
        print("Cache missing")

if __name__ == "__main__":
    run_injection()
