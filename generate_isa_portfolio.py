import requests
import pandas as pd
import json
import os
import base64
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from sovereign_architect import SovereignArchitect, SniperScope

# --- CONFIGURATION ---
API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET", "")
BASE_URL = "https://live.trading212.com/api/v0/equity"

# Watchlist Data
WATCHLIST_DATA = [
    {"ticker": "MSFT_US_EQ", "target": 420.0, "tier": "1+ (Cyborg)"},
    {"ticker": "GOOGL_US_EQ", "target": 170.0, "tier": "1+ (Cyborg)"},
    {"ticker": "LGEN_UK_EQ", "target": 240.0, "tier": "1 (Sleeper)"},
    {"ticker": "RIO_UK_EQ", "target": 4800.0, "tier": "1 (Sleeper)"}
]

def safe_float(val, default=0.0):
    if val is None: return default
    try:
        return float(val)
    except:
        return default

def get_headers():
    if not API_KEY:
        raise ValueError("[!] CRITICAL: No API Key found. Check Repo Secrets.")
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
    print(f"[>] Sentinel v31.1 Platinum: Starting Audit...")
    
    # 1. EXTERNAL RADAR (SniperScope)
    sniper = SniperScope(WATCHLIST_DATA)
    df_sniper, fx_rate = sniper.scan_targets()
    print(f"[OK] FX Rate (GBP/USD): {fx_rate:.4f}")
    
    # 2. INTERNAL RADAR (T212 API)
    try:
        headers = get_headers()
        print("[>] Fetching Positions...")
        r_pos = requests.get(f"{BASE_URL}/positions", headers=headers)
        if r_pos.status_code == 401:
            print("[!] Authentication Failed. Key is invalid.")
            return
        elif r_pos.status_code != 200:
            print(f"[!] API Error: {r_pos.text}")
            return
        positions = r_pos.json()
        
        print("[>] Fetching Account Summary...")
        r_cash = requests.get(f"{BASE_URL}/account/summary", headers=headers)
        summary = r_cash.json()
        
    except Exception as e:
        print(f"[!] Connection Error: {e}")
        return

    # 3. COMPUTATION (Architect)
    arch = SovereignArchitect(fx_rate)
    processed_holdings = []
    
    for p in positions:
        instr = p.get('instrument', {})
        ticker = instr.get('ticker', 'UNKNOWN')
        company_name = instr.get('name', ticker)  # v31.3: Extract company name
        shares = safe_float(p.get('quantity'))
        price = safe_float(p.get('currentPrice'))
        avg = safe_float(p.get('averagePricePaid'))
        
        wallet = p.get('walletImpact', {})
        pl_gbp = safe_float(wallet.get('unrealizedProfitLoss'))
        fx_impact_gbp = safe_float(wallet.get('fxImpact'))
        value_gbp = safe_float(wallet.get('currentValue'))
        
        # v31.3: Calculate P/L per share
        pl_per_share_gbp = price - avg
        pl_per_share_pct = ((price - avg) / avg) * 100 if avg > 0 else 0.0
        
        is_us = "_US_EQ" in ticker
        tier = arch.get_tier(ticker)
        
        processed_holdings.append({
            "Ticker": ticker.replace("_US_EQ", "").replace("_UK_EQ", ""),
            "Company": company_name,  # v31.3: Add company name
            "Shares": shares,
            "Price": price,
            "Avg_Price": avg,
            "PL": pl_gbp,
            "FX_Impact": fx_impact_gbp,
            "Tier": tier,
            "Value": value_gbp,
            "Currency": instr.get('currency', 'USD' if is_us else 'GBP'),
            "PL_Per_Share_GBP": pl_per_share_gbp,  # v31.3: P/L per share in £
            "PL_Per_Share_Pct": pl_per_share_pct   # v31.3: P/L per share in %
        })
        
    # 4. SAVE STATE
    state = {
        "meta": {
            "version": "v31.3 Platinum",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fx_rate": fx_rate
        },
        "account": summary,
        "holdings": processed_holdings,
        "sniper": df_sniper.to_dict(orient='records')
    }
    
    # Save CSV locally (G Drive not available on this system)
    # User's other application should look for: c:\Users\steve\Sovereign-Sentinel\ISA_PORTFOLIO.csv
    csv_path = "ISA_PORTFOLIO.csv"
    pd.DataFrame(processed_holdings).to_csv(csv_path, index=False)
    print(f"[OK] ISA_PORTFOLIO.csv saved to {os.path.abspath(csv_path)}")
    
    with open("live_state.json", "w") as f:
        json.dump(state, f, indent=2)
    print("[OK] live_state.json saved successfully.")

if __name__ == "__main__":
    run_audit()
