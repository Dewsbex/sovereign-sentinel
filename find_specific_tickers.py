import json

targets_to_find = [
    "SOFI", "LCID", "META", "DKNG", "BKNG", 
    "RR.L", "AZN.L", "SHEL.L", "BP.L", "HSBA.L", "LLOY.L", "BARC.L", "NG.L", "VOD.L", "TSCO.L"
]

print("🔍 RESOLVING TICKERS IN MASTER LIST...")

with open('data/master_instruments.json', 'r') as f:
    instruments = json.load(f)

# Build lookups
# 1. Exact match on 'shortName' (e.g. "NVDA")
short_map = {i['shortName']: i for i in instruments if 'shortName' in i}
# 2. Exact match on 'name' (for fuzzy check)
name_map = {i['name']: i for i in instruments if 'name' in i}

resolved = {}
missing = []

for t in targets_to_find:
    # 1. Check if it's a Yahoo Ticker like "RR.L" -> ShortName "RR"
    clean_t = t.split('.')[0] # "RR.L" -> "RR"
    
    match = None
    
    # Try exact shortName match with cleaned ticker (RR)
    if clean_t in short_map:
        match = short_map[clean_t]
    
    # If not found, try raw t (SOFI)
    if not match and t in short_map:
        match = short_map[t]
        
    # If not found, try searching by name?
    if not match:
        # Special case for META (Meta Platforms)
        if t == "META":
            # Search for "Meta Platforms" in names
            for i in instruments:
                if "Meta Platforms" in i.get('name', ''):
                    match = i
                    break
    
    if match:
        resolved[t] = match['ticker']
        msg = f"✅ FOUND: {t} -> {match['ticker']} (ShortName: {match.get('shortName')})"
        # print(msg)
        with open('found_tickers.txt', 'a', encoding='utf-8') as log:
            log.write(msg + '\n')
    else:
        missing.append(t)
        msg = f"❌ MISSING: {t}"
        # print(msg)
        with open('found_tickers.txt', 'a', encoding='utf-8') as log:
           log.write(msg + '\n')

# print("\nSUMMARY:")
# print(f"Resolved: {len(resolved)}")
# print(f"Missing: {len(missing)}")
