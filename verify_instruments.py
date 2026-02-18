import sys
import os
import json
from trading212_client import Trading212Client

# ... (imports and meaningful logic same)
output_buffer = []

def log(msg):
    print(msg)
    output_buffer.append(msg)

log("🔍 VERIFYING INSTRUMENTS WITH TRADING 212 API...")
log("===============================================")

client = Trading212Client()

# 1. Sync Master List from T212
log("1. Fetching latest instrument list from Trading 212...")
if not client.sync_master_list():
    log("❌ Failed to sync with T212. Cannot verify.")
    # sys.exit(1) # Don't exit, try to read file anyway
else:
    # Double check file
    if os.path.exists('data/master_instruments.json'):
       with open('data/master_instruments.json', 'r') as f:
           d = json.load(f)
           log(f"   -> File contains {len(d)} records.")

# 2. Load Our Targets (Master Universe)
try:
    with open('data/master_universe.json', 'r') as f:
        universe = json.load(f)
    log(f"2. Loaded {len(universe.get('instruments', []))} candidates from Master Universe.")
except Exception as e:
    log(f"❌ Failed to load master_universe.json: {e}")
    sys.exit(1)

# 3. Validation Loop
log("3. Validating candidates...")
valid_count = 0
invalid = []
non_us = []

# Load the fresh master list for lookup
with open('data/master_instruments.json', 'r') as f:
    t212_instruments = json.load(f)
    
t212_map = {i['ticker']: i for i in t212_instruments}

for item in universe.get('instruments', []):
    ticker = item['ticker']
    expected_ticker = f"{ticker}_US_EQ"
    
    if expected_ticker in t212_map:
        valid_count += 1
    else:
        # Check raw
        if ticker in t212_map:
             log(f"   ⚠️ Found raw '{ticker}' (No _US_EQ needed?) - T212 Ticker: {t212_map[ticker]['ticker']}")
             # If logic blindly adds _US_EQ, this is a bug.
             invalid.append(f"{ticker} (Found as raw, but logic adds _US_EQ)")
        else:
            invalid.append(ticker)

log("-" * 30)
log(f"✅ VERIFIED: {valid_count} / {len(universe['instruments'])} are definitely valid US Equities.")

if invalid:
    log(f"❌ INVALID / NOT FOUND ({len(invalid)}):")
    for i in invalid[:20]: log(f"   - {i}")
    if len(invalid) > 20: log(f"   ... and {len(invalid)-20} more.")
else:
    log("✅ All candidates are valid and tradable on Trading 212.")

log("===============================================")

with open('verify_log.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_buffer))
