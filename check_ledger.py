import csv

with open('current_ledger.csv', 'r', encoding='utf-16') as f:
    reader = csv.DictReader(f)
    
    total_div = 0.0
    total_interest = 0.0
    total_fees = 0.0
    
    for row in reader:
        action = row.get('Action', '')
        total = row.get('Total', '0')
        
        try:
            val = float(str(total).replace('£','').replace('$','').replace(',',''))
        except:
            val = 0.0
            
        if 'Dividend' in action:
            total_div += val
        elif 'Interest' in action:
            total_interest += val
        elif any(x in action.lower() for x in ['fee', 'tax', 'stamp duty']):
            total_fees += val

    print(f"Total Dividends:  £{total_div:,.2f}")
    print(f"Total Interest:   £{total_interest:,.2f}")
    print(f"Total Fees/Taxes: £{total_fees:,.2f}")
    print(f"Net Non-Trade:    £{total_div + total_interest - total_fees:,.2f}")
