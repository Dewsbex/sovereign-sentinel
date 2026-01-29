import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import config
import os
import sys
import time
from datetime import datetime

import yfinance as yf

# ==============================================================================
# CONFIGURATION
# ==============================================================================
API_BASE = "https://live.trading212.com"
OUTPUT_FILENAME = "ISA_PORTFOLIO.csv"

# ==============================================================================
# AUTHENTICATION
# ==============================================================================
def get_auth():
    """Returns valid HTTPBasicAuth object or raises error."""
    api_key = str(config.T212_API_KEY).strip()
    api_secret = str(config.T212_API_SECRET).strip()
    
    if not api_key or not api_secret or api_key == "None" or api_secret == "None":
        print("[!] [ERROR] Missing API Credentials in config.py / .env")
        sys.exit(1)
        
    return HTTPBasicAuth(api_key, api_secret)

# ==============================================================================
# API FUNCTIONS
# ==============================================================================
def fetch_cash(auth):
    """Step 1: Fetch Account Cash"""
    url = f"{API_BASE}/api/v0/equity/account/cash"
    print(f"[>] Fetching Cash from {url}...")
    
    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[X] [ERROR] Failed to fetch cash: {e}")
        sys.exit(1)

def fetch_portfolio(auth):
    """Step 2: Fetch Portfolio Holdings"""
    url = f"{API_BASE}/api/v0/equity/portfolio"
    print(f"[>] Fetching Portfolio from {url}...")
    
    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[X] [ERROR] Failed to fetch portfolio: {e}")
        sys.exit(1)

def fetch_fx_rates():
    """Fetches live GBPUSD rate from yfinance."""
    print("[>] Fetching Live FX Rates (yfinance)...")
    try:
        # GBPUSD=X returns USD per 1 GBP. e.g. 1.25
        ticker = yf.Ticker("GBPUSD=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            rate = hist['Close'].iloc[-1]
            print(f"[OK] FX Rate GBP/USD: {rate:.4f}")
            return rate
        else:
            print("[!] Warning: yfinance returned no data for GBPUSD=X. Using fallback 1.25.")
            return 1.25
    except Exception as e:
        print(f"[!] Warning: FX fetch failed: {e}. Using fallback 1.25.")
        return 1.25

# ==============================================================================
# HELPERS
# ==============================================================================
def safe_float(value, default=0.0):
    """Safely converts value to float, handling None and errors."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# ==============================================================================
# CORE LOGIC
# ==============================================================================
def generate_portfolio_csv():
    start_time = time.time()
    auth = get_auth()
    
    # 1. Fetch Data
    cash_data = fetch_cash(auth)
    portfolio_data = fetch_portfolio(auth)
    gbp_usd_rate = fetch_fx_rates()
    
    # Use safe_float for cash
    cash_free = safe_float(cash_data.get('free'))
    print(f"[OK] Cash Fetched: GBP {cash_free:.2f}")
    print(f"[OK] Portfolio Fetched: {len(portfolio_data)} positions")

    # 2. Process Holdings
    rows = []
    
    for pos in portfolio_data:
        ticker = pos.get('ticker')
        
        # Safe extractions
        quantity = safe_float(pos.get('quantity'))
        avg_price = safe_float(pos.get('averagePrice'))
        current_price = safe_float(pos.get('currentPrice'))
        ppl = safe_float(pos.get('ppl'))       # Real P/L (GBP)
        fx_ppl = safe_float(pos.get('fxPpl'))  # FX Impact (GBP)
        
        # Currency Detection
        if ticker.endswith("_US_EQ"):
            currency = "USD"
        elif ticker.endswith("_UK_EQ") or ticker.endswith(".L") or ticker.endswith("l_EQ"):
            currency = "GBP"
        elif ticker.endswith("_DE_EQ"):
            currency = "EUR"
        else:
            currency = "USD" # Default assumption

        # Value Calculation (Since API omits 'value')
        # Value (£) = Shares * Price * FX_Factor
        
        if currency == "GBP":
            # Rule: UK stocks usually in Pence (GBX), need /100 to get Pounds
            # Check magnitude if needed, but standard is /100
            value_gbp = (quantity * current_price) / 100.0
        elif currency == "USD":
            # Value (USD) = Quantity * Price
            # Value (GBP) = Value (USD) / GBPUSD_Rate
            value_usd = quantity * current_price
            value_gbp = value_usd / gbp_usd_rate
        else:
            # Fallback for EUR or others (simplified: assume 1:1 if unknown or implement per usage)
            # For now, treat as USD approx or 1:1? Let's use 1.0 logic to avoid crash
            value_gbp = quantity * current_price 

        # BOOK COST CALCULATION (The Golden Formula)
        # Book Cost = Current Value (£) - Real P/L (£)
        book_cost_gbp = value_gbp - ppl

        # FETCH MARKET FUNDAMENTALS (yfinance enrichment)
        fundamentals = {'sector': 'Unknown', 'industry': 'Unknown', 'market_cap': None, 'pe': None, 'div_yield': None, 'rating': 'N/A'}
        try:
            # Initialize market intelligence if not already done
            if 'market_intel_engine' not in globals():
                from market_intelligence import MarketIntelligence
                global market_intel_engine
                market_intel_engine = MarketIntelligence()
            
            # Get comprehensive data
            intel = market_intel_engine.get_comprehensive_data(ticker.split('_')[0])
            fundamentals = {
                'sector': intel.get('fundamentals', {}).get('sector', 'Unknown'),
                'industry': intel.get('fundamentals', {}).get('industry', 'Unknown'),
                'market_cap': intel.get('fundamentals', {}).get('market_cap'),
                'pe': intel.get('fundamentals', {}).get('trailing_pe'),
                'div_yield': intel.get('dividends', {}).get('yield'),
                'rating': intel.get('analyst_ratings', {}).get('consensus', 'none')
            }
        except:
            pass  # Use defaults if fetch fails

        row = {
            "Ticker": ticker,
            "Status": "Holding",
            "Shares": quantity,
            "Avg Price (Local)": avg_price,
            "Live Price (Local)": current_price,
            "Currency": currency,
            "Book Cost (£)": round(book_cost_gbp, 2),
            "Real P/L (£)": round(ppl, 2),
            "FX Impact (£)": round(fx_ppl, 2),
            # NEW: Fundamentals columns
            "Sector": fundamentals['sector'],
            "Industry": fundamentals['industry'],
            "Market Cap": fundamentals['market_cap'] or 0,
            "P/E Ratio": fundamentals['pe'] or 0,
            "Dividend Yield": f"{fundamentals['div_yield']*100:.2f}%" if fundamentals['div_yield'] else "0.00%",
            "Analyst Rating": fundamentals['rating'].upper()
        }
        rows.append(row)

    # 3. Add Cash Row
    cash_row = {
        "Ticker": "CASH_GBP",
        "Status": "Liquidity",
        "Shares": 1,
        "Avg Price (Local)": cash_free, 
        "Live Price (Local)": cash_free, 
        "Currency": "GBP",
        "Book Cost (£)": round(cash_free, 2),
        "Real P/L (£)": 0.00,
        "FX Impact (£)": 0.00
    }
    rows.append(cash_row)
    
    # 4. Create DataFrame
    df = pd.DataFrame(rows)
    
    # Ensure Column Order matches Spec exactly
    cols = [
        "Ticker", "Status", "Shares", "Avg Price (Local)", "Live Price (Local)",
        "Currency", "Book Cost (£)", "Real P/L (£)", "FX Impact (£)",
        "Sector", "Industry", "Market Cap", "P/E Ratio", "Dividend Yield", "Analyst Rating"
    ]
    df = df[cols]

    # 5. Save to File
    save_file(df)
    
    print(f"\n[TIME] Completed in {time.time() - start_time:.2f} seconds")

def save_file(df):
    """Determines save location and writes CSV."""
    
    # Possible paths
    user_home = os.path.expanduser("~")
    paths = [
        "G:/My Drive/",
        os.path.join(user_home, "Google Drive"),
        "." # Local fallback
    ]
    
    save_dir = "."
    for path in paths:
        if os.path.exists(path):
            save_dir = path
            break
            
    full_path = os.path.join(save_dir, OUTPUT_FILENAME)
    
    try:
        df.to_csv(full_path, index=False)
        print(f"\n[SUCCESS] File saved to: {os.path.abspath(full_path)}")
        
        # Verify columns
        print("   Columns: " + ", ".join(df.columns))
    except Exception as e:
        print(f"\n[X] [ERROR] Failed to save file to {full_path}: {e}")
        # Try local fallback if drive failed
        if save_dir != ".":
            print("   Attempting local save...")
            try:
                df.to_csv(OUTPUT_FILENAME, index=False)
                print(f"[SUCCESS] SAVED LOCALLY: {os.path.abspath(OUTPUT_FILENAME)}")
            except Exception as e2:
                 print(f"[X] [CRITICAL] Local save also failed: {e2}")

if __name__ == "__main__":
    print("==================================================")
    print("      TRADING 212 ISA PORTFOLIO GENERATOR")
    print("==================================================")
    generate_portfolio_csv()
