
import os
import sys
import json
import logging
import datetime
import yfinance as yf
from main_bot import Strategy_ORB

# Force logging to console
logging.basicConfig(level=logging.INFO)

def run_backfill():
    print("🚀 Starting Manual Backfill...")
    bot = Strategy_ORB()
    
    # We know these qualified earlier today based on user's screenshots
    targets = ["SMCI", "COIN", "MSTR", "QCOM", "CRM", "NVDA", "AMD"]
    
    # Bypass scan and force the list
    bot.watchlist = targets
    for t in targets:
        bot.avg_vol_lookup[t] = 5000000 # Assume healthy volume for backfill
    
    print(f"Forcing Watchlist: {bot.watchlist}")
    
    bot.monitor_observation_window()
    bot.save_intel()
    
    # Manually check the file
    with open('data/orb_intel.json', 'r') as f:
        data = json.load(f)
        print(f"Intel Targets: {len(data.get('targets', []))}")
        if data.get('targets'):
            print("✅ SUCCESS: Intel populated.")
        else:
            print("❌ FAILURE: Intel empty.")

if __name__ == "__main__":
    run_backfill()
