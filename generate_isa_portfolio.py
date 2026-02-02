import requests, json, os, base64, subprocess, yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET")
BASE_URL = "https://live.trading212.com/api/v0/equity"



def run_audit():
    print("[>] Sentinel v32.15: Sovereign Finality...")
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
        # v32.14: Precise Schema Mapping
        instr = p.get('instrument', {})
        wallet = p.get('walletImpact', {})
        raw_ticker = instr.get('ticker', 'UNKNOWN')
        name = instr.get('name', raw_ticker)
        currency = instr.get('currency', 'GBP')
        
        # 1. Ticker Cleaning
        ticker_clean = raw_ticker.replace("_US_EQ", "").replace("_UK_EQ", "").replace("l_EQ", "").replace("L_EQ", "")
        
        # 2. Manual Normalization (Sovereign Guard Rule)
        qty = p.get('quantity', 0.0)
        raw_price = p.get('currentPrice', 0.0)
        raw_avg = p.get('averagePricePaid', 0.0)
        
        # 3. Currency Normalization (The Fix)
        # If currency is USD, we must convert to GBP.
        fx_rate = 1.0
        if currency == 'USD':
            fx_rate = usd_to_gbp
        
        # v32.14: STRICT UNIT NORMALIZATION (The Sovereign Guard Rule)
        # 1. Normalize Units (Pence -> Pounds) based on Ticker Symbol
        price_instr = normalize_uk_assets(raw_price, raw_ticker)
        avg_price_instr = normalize_uk_assets(raw_avg, raw_ticker)
        
        # 2. Normalize Currency (USD -> GBP)
        price_gbp = price_instr * fx_rate
        avg_price_gbp = avg_price_instr * fx_rate
        
        # Calculate Values 
        val_gbp = price_gbp * qty
        
        # Prefer API's PPL if available (Accurate Realized/Unrealized in GBP)
        # But for consistency with our verified manual calc, we stick to our calc for now unless API is needed.
        # Given "Fault: Unit Inflation", our manual calc is safer if we control inputs.
        pl_gbp = (price_gbp - avg_price_gbp) * qty
        
        # API PPL might be in Pence for UK stocks? Let's treat our calc as Truth.

        total_value_gbp += val_gbp
        
        # v32.13: Enforce Normalized Values in State
        holdings.append({
            "Ticker": ticker_clean,
            "Name": name,
            "Value_GBP": val_gbp,   
            "Value": val_gbp,       
            "Price_GBP": price_gbp, 
            "Price": price_instr,     # Display Instrument Price (e.g. $)
            "Avg_Price": avg_price_instr, # Display Instrument Avg
            "PL_GBP": pl_gbp,       
            "PL": pl_gbp,           
            "Shares": qty,
            "Currency": currency, 
            "FX_Impact": wallet.get('fxImpact', 0.0)
        })

    # Calculate Weights
    for h in holdings:
        h["Weight_Pct"] = (h["Value_GBP"] / total_value_gbp * 100) if total_value_gbp > 0 else 0
        h["Weight"] = h["Weight_Pct"]

    # 4. Sniper / Watchlist Logic (v32.14)
    sniper_data = []
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

    state = {
        "meta": {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "version": "v0.03 Sovereign Finality"},
        "account": acc_summary,
        "holdings": holdings,
        "total_gbp": total_value_gbp,
        "sniper": sniper_data
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
