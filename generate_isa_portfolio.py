import requests, json, os, base64, subprocess, yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET")
BASE_URL = "https://live.trading212.com/api/v0/equity"

def run_audit():
    print("[>] Sentinel v32.6: Implementing API Rules (Key + Secret)...")
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
            pos = []
        else:
            pos = r_pos.json()

        r_acc = requests.get(f"{BASE_URL}/account/info", auth=auth)
        if r_acc.status_code != 200:
            print(f"[API ERROR] Account: {r_acc.status_code}")
            acc = {}
        else:
            acc = r_acc.json()
             
    except Exception as e:
        print(f"[NET ERROR] {e}")
        pos = []
        acc = {}

    # Calculate Total Portfolio Value using v32.5 logic
    total_portfolio_value = sum([p['currentPrice'] * p['quantity'] for p in pos]) if pos else 0
    
    processed_holdings = []
    print(f"[>] Syncing metadata for {len(pos)} assets...")
    
    for p in pos:
        t = p.get('ticker', 'UNKNOWN')
        yf_t = t.replace("_UK_EQ", ".L").replace("_US_EQ", "")
        
        # Metadata Sync (Force fallback to Ticker if Yahoo fails)
        try:
            full_name = yf.Ticker(yf_t).info.get('shortName', t)
        except:
            full_name = t 

        val = p['currentPrice'] * p['quantity']
        shares = p['quantity']
        # Derive Avg Price
        invested = val - p['ppl']
        avg_price = invested / shares if shares > 0 else 0

        processed_holdings.append({
            "Ticker": t.replace("_US_EQ", "").replace("_UK_EQ", ""),
            "Name": full_name,  # <--- CRITICAL KEY v32.5
            "Value": val,      # <--- CRITICAL KEY v32.5
            "Weight": (val / total_portfolio_value) * 100 if total_portfolio_value > 0 else 0,
            "PL": p['ppl'],
            "Price": p['currentPrice'],
            "Shares": shares,
            "Avg_Price": avg_price,
            "Currency": p.get('currency', 'GBP')
        })

    # Save to live_state.json
    state_file = "live_state.json"
    print(f"[>] Saving state to {state_file}...")
    with open(state_file, "w") as f:
        json.dump({"meta": {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")}, "account": acc, "holdings": processed_holdings}, f)

    # 🤖 AUTO-DEPLOY Hand-off
    print("[>] Triggering Auto-Deploy...")
    try:
        subprocess.run(["python", "generate_static.py"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        # Check if anything to commit
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if status:
            subprocess.run(["git", "commit", "-m", "v32.5 Platinum - Unified Data Contract"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("[SUCCESS] Deployment Handled by Antigravity.")
        else:
            print("[INFO] Nothing to commit (clean working tree).")
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Deployment Error: {e}")

if __name__ == "__main__":
    run_audit()
