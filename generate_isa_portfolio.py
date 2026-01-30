import requests, json, os, base64, subprocess, yfinance as yf
from datetime import datetime
from sovereign_architect import SovereignArchitect
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("T212_API_KEY")
BASE_URL = "https://live.trading212.com/api/v0/equity"

def run_audit():
    print("[>] Sentinel v32.4: Syncing Data & Names...")
    if not API_KEY:
        print("[ERROR] T212_API_KEY Missing!")
        return

    # v32.4 Fix: Auth Method Trial (Direct Key)
    headers = {"Authorization": API_KEY}
    
    try:
        # v32.4 Fix: Correct Endpoints & Debug
        r_pos = requests.get(f"{BASE_URL}/portfolio", headers=headers)
        if r_pos.status_code != 200:
            print(f"[API ERROR] Positions: {r_pos.status_code} - {r_pos.text[:100]}")
            pos = []
        else:
            pos = r_pos.json()

        r_acc = requests.get(f"{BASE_URL}/account/info", headers=headers)
        if r_acc.status_code != 200:
            print(f"[API ERROR] Account: {r_acc.status_code} - {r_acc.text[:100]}")
            acc = {}
        else:
            acc = r_acc.json()
        
        # Handle API errors
        if isinstance(pos, dict) and 'code' in pos:
             print(f"[API ERROR] {pos}")
             pos = []
             
    except Exception as e:
        print(f"[NET ERROR] {e}")
        pos = []
        acc = {}

    total_val = sum([p['currentPrice'] * p['quantity'] for p in pos]) if pos else 0
    
    processed = []
    # 📡 Metadata Sync
    print(f"[>] Syncing metadata for {len(pos)} assets...")
    for p in pos:
        ticker = p.get('ticker', 'UNKNOWN')
        yf_t = ticker.replace("_UK_EQ", ".L").replace("_US_EQ", "")
        
        # Try to get better name
        name = ticker
        try:
            # Quick manual map for reliability to avoid slow YF calls if possible or for known issues
            manual_map = {
                "RE": "Everest Group, Ltd.",
                "QELL": "Qell Acquisition Corp.",
                "MP": "MP Materials Corp."
            }
            clean_t = ticker.replace("_US_EQ","").replace("_UK_EQ","")
            
            if clean_t in manual_map:
                name = manual_map[clean_t]
            else:
                # Optionally use yfinance, but it can be slow in loop. 
                # For v32.4 speed, we'll try basic YF info only if critical, 
                # or rely on what we have. 
                # User script requested YF usage:
                t_info = yf.Ticker(yf_t).info
                name = t_info.get('shortName', ticker)
        except: 
            name = ticker

        val = p['currentPrice'] * p['quantity']
        shares = p['quantity']
        # Derive Avg Price if not explicit: (Value - PL) / Shares
        invested = val - p['ppl']
        avg_price = invested / shares if shares > 0 else 0

        processed.append({
            "Ticker": ticker.replace("_US_EQ", "").replace("_UK_EQ", ""),
            "Name": name,
            "Price": p['currentPrice'],
            "Value": val,
            "Weight": (val / total_val) * 100 if total_val > 0 else 0,
            "PL": p['ppl'],
            "Shares": shares,
            "Avg_Price": avg_price,
            "Currency": p.get('currency', 'GBP') # Better guess or from API if avail
        })

    # Save current state
    state_file = "live_state.json"
    print(f"[>] Saving state to {state_file}...")
    with open(state_file, "w") as f:
        json.dump({"meta": {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")}, "account": acc, "holdings": processed}, f)

    # 🤖 AUTO-DEPLOY Hand-off
    print("[>] Triggering Auto-Deploy...")
    try:
        subprocess.run(["python", "generate_static.py"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        # Check if anything to commit
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if status:
            subprocess.run(["git", "commit", "-m", "v32.4 - Perfect Ring Fix"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("[SUCCESS] Deployment Handled by Antigravity.")
        else:
            print("[INFO] Nothing to commit (clean working tree).")
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Deployment Error: {e}")

if __name__ == "__main__":
    run_audit()
