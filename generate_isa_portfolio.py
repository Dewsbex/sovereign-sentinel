import requests
import pandas as pd
import json
import os
import base64
from datetime import datetime
from sovereign_architect import SovereignArchitect, SniperScope

# --- CONFIGURATION ---
# We grab the key injected by the YAML file above
API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET", "") # Default to empty if not needed
BASE_URL = "https://live.trading212.com/api/v0/equity"

# Watchlist Data
WATCHLIST_DATA = [
    {"ticker": "MSFT_US_EQ", "target": 420.0, "tier": "1+ (Cyborg)"},
    {"ticker": "GOOGL_US_EQ", "target": 170.0, "tier": "1+ (Cyborg)"},
    {"ticker": "LGEN_UK_EQ", "target": 240.0, "tier": "1 (Sleeper)"},
    {"ticker": "RIO_UK_EQ", "target": 4800.0, "tier": "1 (Sleeper)"}
]

def get_headers():
    if not API_KEY:
        # This will show in GitHub Action logs if it fails
        raise ValueError("❌ CRITICAL: No API Key found. Check Repo Secrets.")
    
    # Handle keys that don't need a secret (older keys) vs new ones
    if API_SECRET:
        creds = f"{API_KEY}:{API_SECRET}"
    else:
        creds = f"{API_KEY}:"
        
    encoded = base64.b64encode(creds.encode("utf-8")).decode("utf-8")
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json"
    }

def run_audit():
    print(f"🚀 Sentinel v31.1: Starting Audit...")
    
    # 1. EXTERNAL RADAR (SniperScope)
    sniper = SniperScope(WATCHLIST_DATA)
    df_sniper, fx_rate = sniper.scan_targets()
    print(f"✅ FX Rate (GBP/USD): {fx_rate:.4f}")
    
    # 2. INTERNAL RADAR (T212 API)
    try:
        headers = get_headers()
        
        # Fetch Positions
        print("📡 Fetching Positions...")
        r_pos = requests.get(f"{BASE_URL}/positions", headers=headers)
        if r_pos.status_code == 401:
            print("❌ Authentication Failed. Key is invalid.")
            return
        elif r_pos.status_code != 200:
            print(f"❌ API Error: {r_pos.text}")
            return
        positions = r_pos.json()
        
        # Fetch Cash Summary
        print("📡 Fetching Account Summary...")
        r_cash = requests.get(f"{BASE_URL}/account/summary", headers=headers)
        summary = r_cash.json()
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 3. COMPUTATION (Architect)
    arch = SovereignArchitect(fx_rate)
    processed_holdings = []
    
    for p in positions:
        ticker = p.get('ticker', 'UNKNOWN')
        shares = p.get('quantity', 0)
        price = p.get('currentPrice', 0)
        avg = p.get('averagePrice', 0)
        pl = p.get('ppl', 0)
        
        is_us = "_US_EQ" in ticker
        
        tier = arch.get_tier(ticker)
        fx_impact = arch.calculate_fx_impact(pl, price, avg, shares, is_us)
        
        processed_holdings.append({
            "Ticker": ticker.replace("_US_EQ", "").replace("_UK_EQ", ""),
            "Shares": shares,
            "Price": price,
            "Avg_Price": avg,
            "PL": pl,
            "FX_Impact": fx_impact,
            "Tier": tier,
            "Value": price * shares
        })
        
    # 4. SAVE STATE
    state = {
        "meta": {
            "version": "v31.1",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fx_rate": fx_rate
        },
        "account": summary,
        "holdings": processed_holdings,
        "sniper": df_sniper.to_dict(orient='records')
    }
    
    pd.DataFrame(processed_holdings).to_csv("ISA_PORTFOLIO.csv", index=False)
    
    # v31.1: Saving to root as per YAML preference
    with open("live_state.json", "w") as f:
        json.dump(state, f, indent=2)
    print("✅ live_state.json saved successfully.")

if __name__ == "__main__":
    run_audit()
