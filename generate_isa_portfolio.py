import requests, json, os, base64, subprocess, yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET")
BASE_URL = "https://live.trading212.com/api/v0/equity"



def run_audit():
    print("[>] Sentinel v32.8: Sovereign Guard Patch...")
    if not API_KEY or not API_SECRET:
        print("[ERROR] Credentials (Key or Secret) Missing!")
        return

    # v32.6: Correct Auth Pattern (Basic Auth with Secret)
    auth = HTTPBasicAuth(API_KEY, API_SECRET)
    
    try:
        # Correct Endpoints (v32.8 Official Spec)
        r_pos = requests.get(f"{BASE_URL}/positions", auth=auth)
        if r_pos.status_code != 200:
            print(f"[API ERROR] Positions: {r_pos.status_code}")
            pos_data = []
        else:
            pos_data = r_pos.json()

        r_acc = requests.get(f"{BASE_URL}/account/summary", auth=auth)
        if r_acc.status_code != 200:
            print(f"[API ERROR] Account Summary: {r_acc.status_code}")
            acc_summary = {}
        else:
            acc_summary = r_acc.json()
             
    except Exception as e:
        print(f"[NET ERROR] {e}")
        pos_data = []
        acc_summary = {}

    total_value_gbp = 0
    holdings = []

    print(f"[>] Syncing metadata for {len(pos_data)} assets...")
    
    # helper for v32.8 Sovereign Guard
    def get_clean_value(raw_val, ticker):
        if "_UK_EQ" in ticker:
            return float(raw_val) / 100.0
        return float(raw_val)

    # 1. First Pass: Aggregate Normalized Data
    total_value_gbp = 0
    holdings = []

    for p in pos_data:
        # v32.9: Parse Nested API Structure
        instr = p.get('instrument', {})
        # Note: walletImpact is available but user requested manual normalization fix
        
        raw_ticker = instr.get('ticker', 'UNKNOWN')
        name = instr.get('name', raw_ticker)
        
        # 1. Ticker Cleaning
        ticker_clean = raw_ticker.replace("_US_EQ", "").replace("_UK_EQ", "").replace("l_EQ", "").replace("L_EQ", "")
        
        # 2. Value & PL (Manual Sovereign Guard Logic)
        qty = p.get('quantity', 0.0)
        raw_price = p.get('currentPrice', 0.0)
        
        # Explicit Pence Bug Fix
        price_gbp = get_clean_value(raw_price, raw_ticker)
        val_gbp = price_gbp * qty
        
        # Calculate P/L manually to strictly follow price normalization
        avg_price = p.get('averagePricePaid', 0.0)
        avg_price_gbp = get_clean_value(avg_price, raw_ticker)
        pl_gbp = (price_gbp - avg_price_gbp) * qty

        total_value_gbp += val_gbp

        holdings.append({
            "Ticker": ticker_clean,
            "Name": name,
            "Value_GBP": val_gbp,   
            "Value": val_gbp,       
            "Price_GBP": price_gbp, 
            "Price": raw_price,     
            "PL_GBP": pl_gbp,       
            "PL": pl_gbp,           
            "Shares": qty,
            "Average_Price": avg_price,
            "Currency": instr.get('currency', 'GBP'), 
            "FX_Impact": p.get('walletImpact', {}).get('fxImpact', 0.0)
        })

    # Calculate Weights after total is known
    for h in holdings:
        h["Weight_Pct"] = (h["Value_GBP"] / total_value_gbp * 100) if total_value_gbp > 0 else 0
        h["Weight"] = h["Weight_Pct"]

    state = {
        "meta": {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "version": "v32.11"},
        "account": acc_summary,
        "holdings": holdings,
        "total_gbp": total_value_gbp
    }

    # Save to live_state.json
    state_file = "live_state.json"
    print(f"[>] Saving state to {state_file}...")
    with open(state_file, "w") as f:
        json.dump(state, f, indent=4)

    # 🤖 AUTO-DEPLOY Hand-off
    print("[>] Triggering Auto-Deploy...")
    try:
        subprocess.run(["python", "generate_static.py"], check=True)
        subprocess.run(["git", "add", "."], check=True)

        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if status:
            subprocess.run(["git", "commit", "-m", "v32.8 Platinum - Sovereign Guard Patch"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("[SUCCESS] Deployment Handled by Antigravity.")
        else:
            print("[INFO] Nothing to commit (clean working tree).")
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Deployment Error: {e}")

if __name__ == "__main__":
    run_audit()
