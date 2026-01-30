import requests
import pandas as pd
import json
import os
import base64
import glob
import subprocess
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import yfinance as yf
from sovereign_architect import SovereignArchitect, SniperScope

# --- CONFIGURATION ---
API_KEY = os.environ.get("T212_API_KEY")
API_SECRET = os.environ.get("T212_API_SECRET", "")
BASE_URL = "https://live.trading212.com/api/v0/equity"

# --- THE KNOWLEDGE BRIDGE (Notebook LM Sync) ---
LOCAL_KNOWLEDGE_PATH = r"G:\My Drive\NotebookLM Sync"

# Watchlist Data (v32.4 - Intelligence Integrated)
WATCHLIST_DATA = [
    {
        "ticker": "MP_US_EQ", 
        "target": 25.0, 
        "tier": "1+ (Strategic)", 
        "tags": ["Rare Earths", "Mining"],
        "default_thesis": "Policy Premium Play. US Dept of War equity position."
    },
    {
        "ticker": "RIO_UK_EQ", 
        "target": 4800.0, 
        "tier": "1 (Standard)", 
        "tags": ["Copper", "Mining"],
        "default_thesis": "Copper Shortage. Supply cuts at Escondida/Grasberg."
    },
    {
        "ticker": "NFLX_US_EQ", 
        "target": 80.0, 
        "tier": "2 (Watch)", 
        "tags": ["Streaming", "Tech"],
        "default_thesis": "Bearish Divergence. Targets falling despite Buy ratings."
    },
    {
        "ticker": "MSFT_US_EQ", 
        "target": 420.0, 
        "tier": "1+ (Cyborg)",
        "tags": ["AI", "Cloud"],
        "default_thesis": "AI dominance via Azure/OpenAI integration remains unparalleled."
    }
]

class KnowledgeBase:
    def __init__(self, data_path):
        self.data_path = data_path

    def get_latest_intel(self, ticker, tags=[]):
        """Scans G: Drive for files matching the Ticker or Tags."""
        if not os.path.exists(self.data_path):
            return None, None

        clean_ticker = ticker.split('_')[0]
        search_terms = [clean_ticker] + tags
        
        found_file = None
        all_files = glob.glob(os.path.join(self.data_path, "*.txt"))
        
        for term in search_terms:
            for f in all_files:
                filename = os.path.basename(f).lower()
                if term.lower() in filename:
                    found_file = f
                    break
            if found_file: break
        
        if not found_file: return None, None

        try:
            with open(found_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Grab the first 300 characters as the summary
                snippet = content[:300].replace('\n', ' ').strip() + "..."
                return snippet, os.path.basename(found_file)
        except Exception as e:
            print(f"[!] Intel Read Error: {e}")
            return None, None

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

def update_history_log(total_value):
    """Appends current value to history log for real-time tracking."""
    log_path = "data/history_log.json"
    os.makedirs("data", exist_ok=True)
    
    history = []
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    # Add current point
    now_ts = int(datetime.now().timestamp() * 1000) # MS for ApexCharts
    history.append([now_ts, total_value])
    
    # Keep last 10,000 points (approx 3 months at 15m intervals)
    # We use backfill for 1Y daily data, but log for high-res 1D/1W view
    if len(history) > 10000:
        history = history[-10000:]
        
    with open(log_path, 'w') as f:
        json.dump(history, f)

def backfill_history(holdings, cash, fx_rate):
    """Generates 1Y of simulated history based on current holdings."""
    log_path = "data/history_log.json"
    
    # We allow backfill if file doesn't exist OR is very small (likely Just current point)
    if os.path.exists(log_path) and os.path.getsize(log_path) > 1000:
        return

    print("[>] History log missing. Generating 1Y Bionic History...")
    
    tickers = []
    ticker_shares = {}
    for h in holdings:
        t_raw = h['Ticker']
        # Clean for YF
        if ".L" in t_raw: yf_t = t_raw
        elif "_US" in t_raw: yf_t = t_raw.replace("_US", "")
        else: yf_t = t_raw
        
        tickers.append(yf_t)
        ticker_shares[yf_t] = h['Shares']
    
    if not tickers:
        return

    try:
        # Fetch 1Y history for all
        data = yf.download(tickers + ["GBPUSD=X"], period="1y", interval="1d", progress=False)['Close']
        
        simulated_history = []
        for timestamp, row in data.iterrows():
            total_val_gbp = cash
            fx = row.get("GBPUSD=X", fx_rate)
            
            for t, shares in ticker_shares.items():
                price = row.get(t, 0.0)
                if pd.isna(price) or price == 0: continue
                
                # Convert to GBP if USD
                if any(ext in t for ext in [".L", "UK"]):
                    # GBp (pence) to GBP
                    val = (shares * price) / 100 if price > 10 else (shares * price)
                    # Actually yfinance .L is usually GBp. Simple check:
                else:
                    # USD to GBP
                    val = (shares * price) / fx
                
                total_val_gbp += val
            
            ts_ms = int(timestamp.timestamp() * 1000)
            if not pd.isna(total_val_gbp):
                simulated_history.append([ts_ms, round(total_val_gbp, 2)])
        
        with open(log_path, 'w') as f:
            json.dump(simulated_history, f)
        print(f"[OK] Bionic History generated: {len(simulated_history)} points.")
        
    except Exception as e:
        print(f"[WARN] Backfill failed: {e}")

def deploy_to_github():
    """
    🤖 ANTIGRAVITY AUTOMATION: Pushes the code to GitHub automatically.
    """
    print("\n[AUTO-DEPLOY] Handing off to GitHub...")
    try:
        # 1. Stage all files
        subprocess.run(["git", "add", "."], check=True)
        
        # 2. Commit (Timestamped)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        msg = f"Antigravity Auto-Update: {ts}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        
        # 3. Push
        subprocess.run(["git", "push"], check=True)
        print("[SUCCESS] Uploaded to GitHub. Cloudflare will sync in ~60s.")
        
    except subprocess.CalledProcessError as e:
        print(f"[GIT ERROR] {e}")
        print("Tip: Check if you have unmerged changes or network issues.")

def run_audit():
    print(f"[>] Sentinel v32.12 Master: Zero-Touch Automation...")
    
    # 0. KNOWLEDGE BRIDGE SCAN (v32.4)
    print("[>] Scanning Knowledge Base...")
    kb = KnowledgeBase(LOCAL_KNOWLEDGE_PATH)
    for target in WATCHLIST_DATA:
        intel_text, source = kb.get_latest_intel(target['ticker'], target.get('tags', []))
        if intel_text:
            target['hypothesis'] = intel_text
            target['source'] = source
        else:
            target['hypothesis'] = target.get('default_thesis', "No recent intelligence found.")
            target['source'] = "Sentinel Default"

    # 1. EXTERNAL RADAR (SniperScope)
    sniper = SniperScope(WATCHLIST_DATA)
    df_sniper, fx_rate = sniper.scan_targets()
    print(f"[OK] FX Rate (GBP/USD): {fx_rate:.4f}")
    
    # v32.10: Apply Robust Metadata to Sniper List
    if not df_sniper.empty:
        def clean_sniper_name(row):
            t = row.get('t212_ticker', row.get('ticker', ''))
            # 1. Clean Ticker Display
            clean_t = t.replace("_UK_EQ", "").replace("_US_EQ", "")
            # 2. Try to get a better name if it's currently just the ticker
            curr_name = row.get('name', t)
            if curr_name == t or curr_name == clean_t or "_EQ" in curr_name:
                # Basic cleaned ticker is better than raw
                return clean_t
            return curr_name

        df_sniper['t212_ticker'] = df_sniper['t212_ticker'].apply(lambda x: x.replace("_UK_EQ", "").replace("_US_EQ", ""))
        df_sniper['name'] = df_sniper.apply(clean_sniper_name, axis=1)
    
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

    # 3. BATCH METADATA (v32.8: Robust Resolution)
    print(f"[>] Fetching Company Metadata (Batch)...")
    
    # Cleaning Logic
    def clean_ticker(t):
        if "l_EQ" in t: return t.replace("l_EQ", ".L") 
        return t.replace("_UK_EQ", ".L").replace("_US_EQ", "")
    
    # Restore Definition
    holdings_tickers = [p.get('instrument', {}).get('ticker') for p in positions]
    yf_tickers = [clean_ticker(t) for t in holdings_tickers if t]
    
    # Manual Override Map for Stubborn Tickers
    manual_overrides = {
        "RE": "Everest Group, Ltd.",
        "QELL": "Qell Acquisition Corp."
    }

    company_names = {}
    
    try:
        # 1. Batch Fetch
        info_data = yf.Tickers(" ".join(yf_tickers))
        
        for t_raw, t_yf in zip(holdings_tickers, yf_tickers):
            # Check Manual Override first
            if t_yf in manual_overrides:
                company_names[t_raw] = manual_overrides[t_yf]
                continue
                
            try:
                # Try batch result
                name = info_data.tickers[t_yf].info.get('shortName')
                
                # If Batch Failed, Retry Individual
                if not name or name == t_yf:
                    print(f"    [~] Retrying {t_raw} -> {t_yf} individually...")
                    name = yf.Ticker(t_yf).info.get('shortName', t_raw)
                    
                company_names[t_raw] = name
            except Exception as e:
                print(f"    [!] Meta Fail for {t_raw}: {e}")
                company_names[t_raw] = t_raw
    except Exception as e:
        print(f"⚠️ Metadata Error: {e}")

    # 4. COMPUTATION (Architect)
    arch = SovereignArchitect(fx_rate)
    # Process Holdings
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
        
        # v32.3: Allocation Metadata
        name = company_names.get(ticker, company_name)
        val_gbp = value_gbp
        
        is_us = "_US_EQ" in ticker
        tier = arch.get_tier(ticker)
        
        processed_holdings.append({
            "Ticker": ticker.replace("_US_EQ", "").replace("_UK_EQ", ""),
            "Company": name,  # v32.3: Use fetched shortName
            "Shares": shares,
            "Price": price,
            "Avg_Price": avg,
            "PL": pl_gbp,
            "FX_Impact": fx_impact_gbp,
            "Tier": tier,
            "Value": value_gbp,
            "Currency": instr.get('currency', 'USD' if is_us else 'GBP'),
            "PL_Per_Share_GBP": pl_per_share_gbp,
            "PL_Per_Share_Pct": pl_per_share_pct
        })

    # v32.3: Weight Calculation and Sorting
    total_val_p = sum([h['Value'] for h in processed_holdings])
    for h in processed_holdings:
        h['Weight'] = (h['Value'] / total_val_p) * 100 if total_val_p > 0 else 0
        
    processed_holdings.sort(key=lambda x: x['Value'], reverse=True)
        
    # 4. SAVE STATE (v32.6)
    state = {
        "meta": {
            "version": "v32.6 Platinum",
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
    
    # 5. HISTORY ENGINE (v31.7)
    total_val = safe_float(summary.get('totalValue'))
    
    # Backfill first if needed
    if not os.path.exists("data/history_log.json") or os.path.getsize("data/history_log.json") < 1000:
        backfill_history(processed_holdings, safe_float(summary.get('cash', {}).get('availableToTrade')), fx_rate)
        
    update_history_log(total_val)

    # --- THE TRIGGER (v32.11) ---
    print("[SUCCESS] Data Audit Complete. Triggering Artist...")
    
    # 1. Run The Artist (Job B)
    subprocess.run(["python", "generate_static.py"], check=True)
    
    # 2. Deploy to Cloud
    deploy_to_github()

if __name__ == "__main__":
    run_audit()
