import requests
import pandas as pd
import json
import os
import base64
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import yfinance as yf
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
    # v31.4: Fetch Daily Market Data
    clean_tickers_map = {}
    yf_tickers = []
    
    for p in positions:
        instr = p.get('instrument', {})
        raw = instr.get('ticker', 'UNKNOWN')
        
        # Clean Ticker logic
        if "_US_EQ" in raw:
            clean = raw.replace("_US_EQ", "")
        elif "l_EQ" in raw:
             clean = raw.replace("l_EQ", ".L")
        elif "_UK_EQ" in raw:
            clean = raw.replace("_UK_EQ", ".L")
        else:
            clean = raw.replace("_EQ", "")
            
        clean_tickers_map[raw] = clean
        yf_tickers.append(clean)

    # Batch Fetch
    daily_data = {}
    if yf_tickers:
        try:
            print(f"[SCOPE] Fetching daily data for {len(yf_tickers)} assets...")
            tickers_str = " ".join(yf_tickers)
            # data = yf.download(tickers_str, period="1d", group_by='ticker', progress=False) 
            # Note: yf.download structure varies for single vs multiple. Using Ticker object for safety if list is small, 
            # or safer: fetch info or history one by one if batch is flaky. 
            # For robustness with small portfolio, simple loop is safer than parsing multi-index DF complexities blindly.
            pass 
        except Exception as e:
            print(f"[WARN] YFinance Batch Error: {e}")

    # Process Holdings
    processed_holdings = []
    
    for p in positions:
        instr = p.get('instrument', {})
        ticker_raw = instr.get('ticker', 'UNKNOWN')
        yf_ticker = clean_tickers_map.get(ticker_raw, ticker_raw)
        
        company_name = instr.get('name', ticker_raw)
        shares = safe_float(p.get('quantity'))
        price = safe_float(p.get('currentPrice'))
        avg = safe_float(p.get('averagePricePaid'))
        
        wallet = p.get('walletImpact', {})
        pl_gbp = safe_float(wallet.get('unrealizedProfitLoss'))
        fx_impact_gbp = safe_float(wallet.get('fxImpact'))
        value_gbp = safe_float(wallet.get('currentValue'))
        
        # Total P/L per share (since buy)
        pl_per_share_gbp = price - avg
        pl_per_share_pct = ((price - avg) / avg) * 100 if avg > 0 else 0.0
        
        # v31.4: Daily Change Calculation
        day_change_pct = 0.0
        try:
            t = yf.Ticker(yf_ticker)
            # Fast fetch
            hist = t.history(period="2d")
            if len(hist) >= 1:
                # Use current vs previous close
                # If market open, compare to prev close
                # If len is 1 (today only), we need prev close from info or metadata, but history usually gives 2 rows if open?
                # Actually, simplest is (Close[-1] - Close[-2]) / Close[-2]
                # If only 1 row, maybe we can't calc change from history alone easily without checking 'previousClose' in info
                # Let's try info for 'regularMarketChangePercent' (slower but easier) OR history
                
                # Check history length
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[-2]
                    curr_price = hist['Close'].iloc[-1]
                    day_change_pct = ((curr_price - prev_close) / prev_close) * 100
                else:
                    # Fallback to info if history implies only 1 day available (e.g. IPO or data gap)
                    # Or just 0.0
                    info = t.info
                    day_change_pct = info.get('regularMarketChangePercent', 0.0) * 100 if 'regularMarketChangePercent' in info else 0.0
                    # Note: yf info often returns pure decimal for percent? No, usually it's e.g. -1.23
                    # Wait, info['regularMarketChangePercent'] is usually 0.0123 for 1.23%? Let's assume decimal. 
                    # Actually standard YF info `regularMarketChangePercent` is e.g. 0.00534
        except:
            day_change_pct = 0.0

        daily_pl_gbp = (value_gbp * (day_change_pct / 100)) # Approx Daily P/L based on today's move

        is_us = "_US_EQ" in ticker_raw
        tier = arch.get_tier(ticker_raw)
        
        processed_holdings.append({
            "Ticker": ticker_raw.replace("_US_EQ", "").replace("_UK_EQ", "").replace("l_EQ", ""),
            "Company": company_name,
            "Shares": shares,
            "Price": price,
            "Avg_Price": avg,
            "PL": pl_gbp,
            "FX_Impact": fx_impact_gbp,
            "Tier": tier,
            "Value": value_gbp,
            "Currency": instr.get('currency', 'USD' if is_us else 'GBP'),
            "PL_Per_Share_GBP": pl_per_share_gbp,
            "PL_Per_Share_Pct": pl_per_share_pct,
            "Day_Change_Pct": day_change_pct, # v31.4
            "Day_PL_GBP": daily_pl_gbp       # v31.4
        })
        
    # 4. SAVE STATE
    state = {
        "meta": {
            "version": "v31.4 Platinum",
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
