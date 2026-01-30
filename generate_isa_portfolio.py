import requests, json, os, base64, subprocess, yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET")
BASE_URL = "https://live.trading212.com/api/v0/equity"

def normalize_to_pounds(value, ticker):
    """
    STRICT NORMALIZATION: Trading 212 often quotes UK stocks in GBX.
    We force divide by 100 for all _UK_EQ tickers to ensure £1.00 is not £100.00.
    """
    if "_UK_EQ" in ticker:
        return float(value) / 100.0
    return float(value)

def run_audit():
    print("[>] Sentinel v32.7: Sovereign Guard (Currency Normalization)...")
    if not API_KEY or not API_SECRET:
        print("[ERROR] Credentials (Key or Secret) Missing!")
        return

    # v32.6: Correct Auth Pattern (Basic Auth with Secret)
    auth = HTTPBasicAuth(API_KEY, API_SECRET)
    
    try:
        # Correct Endpoints (v32.5/6)
        r_pos = requests.get(f"{BASE_URL}/portfolio", auth=auth)
        if r_pos.status_code != 200:
            print(f"[API ERROR] Portfolio: {r_pos.status_code}")
            pos_data = []
        else:
            pos_data = r_pos.json()

        r_acc = requests.get(f"{BASE_URL}/account/info", auth=auth)
        if r_acc.status_code != 200:
            print(f"[API ERROR] Account: {r_acc.status_code}")
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

    for p in pos_data:
        ticker = p.get('ticker', 'UNKNOWN')
        # Metadata Sync for Name: fall back to ticker if yfinance fails
        try:
            name = yf.Ticker(ticker.replace("_US_EQ", "").replace("_UK_EQ", ".L")).info.get('shortName', ticker)
        except:
            name = ticker

        # Apply Sovereign Guard Normalization
        raw_price = p.get('currentPrice', 0)
        price_gbp = normalize_to_pounds(raw_price, ticker)
        qty = p.get('quantity', 0)
        val_gbp = price_gbp * qty # Calculate local GBP value
        
        # PPL Normalization
        ppl_gbp = normalize_to_pounds(p.get('ppl', 0), ticker)
        
        total_value_gbp += val_gbp

        holdings.append({
            "Ticker": ticker.replace("_US_EQ", "").replace("_UK_EQ", ""),
            "Name": name,
            "Value_GBP": val_gbp, # EXPLICIT KEY
            "Price_GBP": price_gbp,
            "PL_GBP": ppl_gbp,
            "Shares": qty,
            # Legacy keys for backward compat if needed, or just standard ones
            "Value": val_gbp,
            "Price": price_gbp
        })

    # Calculate Weights after total is known
    for h in holdings:
        h["Weight_Pct"] = (h["Value_GBP"] / total_value_gbp * 100) if total_value_gbp > 0 else 0
        # Add Weight key for legacy compat if needed
        h["Weight"] = h["Weight_Pct"]

    state = {
        "meta": {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "version": "v32.7"},
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
        # Check if anything to commit
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if status:
            subprocess.run(["git", "commit", "-m", "v32.7 Platinum - Sovereign Guard"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("[SUCCESS] Deployment Handled by Antigravity.")
        else:
            print("[INFO] Nothing to commit (clean working tree).")
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Deployment Error: {e}")

if __name__ == "__main__":
    run_audit()
