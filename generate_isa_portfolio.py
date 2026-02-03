import requests, json, os, base64, subprocess, yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET")
BASE_URL = "https://live.trading212.com/api/v0/equity"



def run_audit():
    print("[>] Sentinel v0.12: Sovereign Finality...")
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
    
    # 1. First Pass: Aggregate Normalized Data
    total_value_gbp = 0
    holdings = []

    # v32.14 Sovereign Finality - Strict Unit Normalization
    def normalize_uk_assets(value, ticker):
        """If the ticker is UK, the T212 API is sending Pence. We need Pounds."""
        if "_UK_EQ" in ticker or ticker.endswith("l_EQ") or ticker.endswith(".L"):
            return float(value) / 100.0
        return float(value)

    # v32.15: Dynamic FX Rate Fetching (Sovereign Finality)
    try:
        gbp_usd_ticker = yf.Ticker("GBPUSD=X")
        gbp_usd_rate = float(gbp_usd_ticker.fast_info['last_price'])
        # Rate is GBP per USD? No, usually GBPUSD=X is USD per GBP (1.26).
        # We need GBP per USD = 1 / 1.26 = 0.79.
        # Let's verify standard quoting. "GBPUSD=X" price is 1.25. (1 GBP = 1.25 USD).
        usd_to_gbp = 1.0 / gbp_usd_rate if gbp_usd_rate > 0 else 0.75
        print(f"[FX] GBPUSD Rate: {gbp_usd_rate:.4f} (1 USD = £{usd_to_gbp:.4f})")
    except Exception as e:
        print(f"[FX] Fetch Failed: {e}. Using fallback 0.79")
        usd_to_gbp = 0.79

    for p in pos_data:
        instr = p.get('instrument', {})
        raw_ticker = instr.get('ticker', 'UNKNOWN')
        name = instr.get('name', raw_ticker)
        currency = instr.get('currency', 'GBP')
        
        # 1. Ticker Cleaning
        ticker_clean = raw_ticker.replace("_US_EQ", "").replace("_UK_EQ", "").replace("l_EQ", "").replace("L_EQ", "")
        
        # 2. Extract Values directly from API (already normalized in GBP for GBP accounts)
        qty = float(p.get('quantity', 0.0))
        
        # v32.17: Fields are nested in walletImpact for latest API schema
        wi = p.get('walletImpact', {})
        val_gbp = float(wi.get('currentValue', 0.0))
        cost_gbp = float(wi.get('totalCost', 0.0))
        pl_gbp = float(wi.get('unrealizedProfitLoss', val_gbp - cost_gbp))

        # Prices for display (keep instrument currency)
        raw_price = float(p.get('currentPrice', 0.0))
        raw_avg = float(p.get('averagePricePaid', 0.0))
        
        price_display = normalize_uk_assets(raw_price, raw_ticker)
        avg_display = normalize_uk_assets(raw_avg, raw_ticker)

        total_value_gbp += val_gbp
        
        holdings.append({
            "Ticker": ticker_clean,
            "Name": name,
            "Value_GBP": val_gbp,   
            "Value": val_gbp,       
            "Price_GBP": val_gbp / qty if qty > 0 else 0, 
            "Price": price_display,     
            "Avg_Price": avg_display, 
            "PL_GBP": pl_gbp,       
            "PL": pl_gbp,           
            "Shares": qty,
            "Currency": currency, 
            "FX_Impact": wi.get('fxImpact', 0.0)
        })

    # Calculate Weights
    for h in holdings:
        h["Weight_Pct"] = (h["Value_GBP"] / total_value_gbp * 100) if total_value_gbp > 0 else 0
        h["Weight"] = h["Weight_Pct"]

    # 4. Sniper / Watchlist Logic (v32.14)
    sniper_data = []
    
    # [A] Titan ORB Targets (High Priority)
    try:
        if os.path.exists('data/trade_state.json'):
            with open('data/trade_state.json', 'r') as f:
                orb_state = json.load(f)
                orb_targets = orb_state.get('targets', [])
                
            print(f"[>] Processing {len(orb_targets)} Active ORB Targets...")
            
            for t in orb_targets:
                ticker = t.get('ticker')
                # Avoid duplicates if watchlist also has it (we'll flag it)
                
                sniper_data.append({
                    "ticker": ticker,
                    "name": ticker, # Name might not be in state, acceptable fallback
                    "t212_ticker": f"{ticker}_US_EQ",
                    "target_price": float(t.get('high', 0)), # Breakout Level
                    "live_price": float(t.get('last_poll_price', 0)),
                    "distance_pct": 0.0, # It's active, so distance is effectively 0 or relevant to breakout
                    "expected_growth": 0,
                    "tier": "1", # ORB targets are Tier 1 by definition of activity
                    "status": "ACTIVE ORB",
                    "source": "Titan ORB"
                })
    except Exception as e:
        print(f"[WARN] ORB State Ingest Failed: {e}")

    # [B] Standard Watchlist
    try:
        if os.path.exists('watchlist.json'):
            with open('watchlist.json', 'r') as f:
                watchlist = json.load(f)
                
            print(f"[>] Processing {len(watchlist)} Sniper targets...")
            
            for item in watchlist:
                ticker = item.get('ticker')
                if not ticker: continue
                
                try:
                    # Fetch live price
                    yf_tick = yf.Ticker(ticker)
                    # fast_info is efficient
                    live_price = float(yf_tick.fast_info['last_price'])
                    
                    target_price = float(item.get('target_price', 0))
                    
                    # Calculate Distance
                    dist = 0.0
                    if target_price > 0:
                        dist = ((live_price - target_price) / target_price) * 100
                        
                    # Status Logic
                    status = "WATCH"
                    if dist <= 1.0 and dist >= -1.0: status = "BUY ZONE"
                    if dist < -5.0: status = "DEEP VALUE"
                    if dist > 10.0: status = "EXTENDED"
                    
                    sniper_data.append({
                        "ticker": ticker,
                        "name": item.get('name', ticker),
                        "t212_ticker": f"{ticker}_US_EQ", # Assumption, logical guess
                        "target_price": target_price,
                        "live_price": live_price,
                        "distance_pct": dist,
                        "expected_growth": item.get('expected_growth', 0),
                        "tier": item.get('tier', '2'),
                        "status": status,
                        "source": "Manual Watchlist"
                    })
                except Exception as e:
                    print(f"[WARN] Sniper Fetch Error {ticker}: {e}")
                    # Include with partial data if possible or skip
                    continue
    except Exception as e:
        print(f"[ERROR] Sniper Logic Failed: {e}")

    # 5. Ingest ORB Intelligence (v0.12)
    orb_intel = {}
    try:
        if os.path.exists('data/orb_intel.json'):
            with open('data/orb_intel.json', 'r') as f:
                orb_intel = json.load(f)
            print(f"[>] Ingested ORB Intelligence Briefing.")
    except Exception as e:
        print(f"[WARN] ORB Intel Ingest Failed: {e}")

    state = {
        "meta": {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "version": "v0.12 Sovereign Finality"},
        "account": acc_summary,
        "holdings": holdings,
        "total_gbp": total_value_gbp,
        "sniper": sniper_data,
        "orb_intel": orb_intel
    }

    # Save to live_state.json
    state_file = "live_state.json"
    print(f"[>] Saving state to {state_file}...")
    with open(state_file, "w") as f:
        json.dump(state, f, indent=4)

    # v32.16: Deployment logic removed from script. 
    # Use sentinel-daemon.yml or manual git commands for deployment.
    pass

if __name__ == "__main__":
    run_audit()
