import os
import requests
import json
import time # Added for rate limiting
from datetime import datetime

# ... (rest of imports/config)

# ==============================================================================
# 0. CONFIGURATION & HELPERS
# ==============================================================================

def clean_ticker(ticker_raw):
    """Normalize tickers by removing exchange suffixes."""
    # UK stocks often come as 'VODl_EQ' or 'RR.L'
    # We want just 'VOD' or 'RR'.
    t = ticker_raw.replace('l_EQ', '').replace('_EQ', '').replace('.L', '')
    return t

def parse_float(value, default=0.0):
    """Safely converts API strings to floats."""
    if value is None: return default
    try:
        # ONLY remove commas and currency symbols. Keep the dot!
        clean = str(value).replace(',', '').replace('$', '').replace('£', '')
        return float(clean)
    except ValueError:
        return default

def make_request_with_retry(url, headers, auth, max_retries=3):
    """
    Wrapper for requests.get that handles 429 Rate Limits with backoff.
    """
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, auth=auth)
            
            if r.status_code == 429:
                wait_time = (attempt + 1) * 5 # 5s, 10s, 15s
                print(f"   [RATE LIMIT 429] Pacing enforcement... Cooling down for {wait_time}s")
                time.sleep(wait_time)
                continue # Retry
                
            return r # Return response (success or other error)
            
        except requests.exceptions.RequestException as e:
            print(f"   [NETWORK ERROR] Attempt {attempt+1}/{max_retries}: {e}")
            time.sleep(2)
            
    # If we exhaust retries, return the last response (or a dummy if completely failed)
    # To be safe, if we have a response object from the last attempt, return it.
    # If we crashed before getting a response (e.g. connection error), return None or mock?
    # Simplified: return None if completely failed
    return None

# ==============================================================================
# 1. MAIN EXECUTION
# ==============================================================================

def main():
    print(f"Starting Sovereign Sentinel... (Re-deploy {datetime.now().strftime('%H:%M:%S')})")
    
    # DEFAULT DATA (Fail-Safe)
    total_value = 0.0
    cash_reserves = 0.0
    projected_income = 0.0
    total_fees_str = "£0.00"
    heatmap_data = []
    architect_audit = []
    t212_error = None  # Track T212 failures explicitly
    
    try:
        # 1. FETCH DATA FROM TRADING 212 (LIVE SERVER ONLY)
        # Load keys from Environment Variables
        api_id = os.environ.get('T212_API_KEY')      # The short ID
        api_secret = os.environ.get('T212_API_SECRET') # The long Secret

        if not api_id or not api_secret:
            print("CRITICAL WARNING: Missing API credentials. Rendering Fallback Mode.")
            # We DONT exit, we just let the try block finish or skip to render
            raise ValueError("Missing API Keys (Check GitHub Secrets)")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SovereignSentinel/1.0",
            "Content-Type": "application/json"
        }
        
        BASE_URL = "https://live.trading212.com/api/v0/"
        print(f"Connecting to LIVE Server: {BASE_URL}")

        # --- METADATA FETCH (PHASE 16) ---
        print("Fetching Instrument Metadata...")
        r_meta = make_request_with_retry(f"{BASE_URL}equity/metadata/instruments", headers=headers, auth=(api_id, api_secret))
        
        instrument_map = {}
        if r_meta and r_meta.status_code == 200:
            meta_data = r_meta.json()
            for item in meta_data:
                t_id = item.get('ticker')
                if t_id:
                    instrument_map[t_id] = {
                        'currency': item.get('currencyCode'),
                        'symbol': item.get('shortName') or item.get('name') or t_id,
                        'type': item.get('type')
                    }
            print(f"Metadata Loaded: {len(instrument_map)} instruments mapped.")
        else:
            code = r_meta.status_code if r_meta else "NET_FAIL"
            print(f"METADATA FAILED: {code} - Continuing with fallback heuristics.")

        time.sleep(1) # Minimal pacing

        # --- ORDER HISTORY (PHASE 18) ---
        print("Fetching Order History...")
        r_orders = make_request_with_retry(f"{BASE_URL}equity/history/orders?limit=100", headers=headers, auth=(api_id, api_secret))
        
        # --- FEE AUDITOR LOGIC (MANUAL FIX) ---
        total_fees = 0.0
        if r_orders and r_orders.status_code == 200:
            history_data = r_orders.json() 
            for order in history_data:
                total_fees += float(order.get('currencyConversionFee', 0) or 0)
                if 'taxes' in order:
                    for tax in order['taxes']:
                        total_fees += float(tax.get('quantity', 0) or 0)

        total_fees_str = f"£{total_fees:,.2f}"
        print(f"Fee Auditor Complete: {total_fees_str}")
        
        time.sleep(1) # Minimal pacing

        # Account Cash/Stats
        r_account = make_request_with_retry(f"{BASE_URL}equity/account/cash", headers=headers, auth=(api_id, api_secret))
        cash_data = r_account.json() if (r_account and r_account.status_code == 200) else {}
        
        time.sleep(1) # Minimal pacing

        r_portfolio = make_request_with_retry(f"{BASE_URL}equity/portfolio", headers=headers, auth=(api_id, api_secret))
        if r_portfolio and r_portfolio.status_code == 200:
            portfolio_raw = r_portfolio.json()
        else:
            portfolio_raw = []
            code = r_portfolio.status_code if r_portfolio else "NET_ERR"
            msg = r_portfolio.text[:50] if r_portfolio else "Connection Failed"
            
            error_msg = f"PORTFOLIO FETCH FAILED: {code} - {msg}"
            print(error_msg)
            
            if not t212_error: t212_error = error_msg
            else: t212_error += f" | {error_msg}"

        # T212 API (Users with GBP accounts): Everything is usually in Pence.
        # 1.5M pence = £15,000.
        total_wealth_raw = parse_float(cash_data.get('total', 0)) / 100.0
        cash_reserves = parse_float(cash_data.get('free', 0)) / 100.0
        
        # Initialize total_value with the account total
        total_value = total_wealth_raw

    # --- SOVEREIGN ARCHITECT LOGIC (PHASE 24) ---
        # "The Math Anchors"
        RISK_FREE_RATE = 0.038 # 3.80%
        US_WHT = 0.15 # 15% Tax Trap
        MIN_HURDLE = 0.043 # 4.3% (3.8 + 0.5 Risk Premium)

        architect_audit = []

        for pos in portfolio_raw:
            raw_ticker = pos.get('ticker', '')
            if not raw_ticker: continue
            
            # 1. Identity
            meta = instrument_map.get(raw_ticker, {})
            ticker = meta.get('symbol') or clean_ticker(raw_ticker)
            currency = meta.get('currency') or pos.get('currency', '')
            
            # 2. Financials (Live)
            qty = parse_float(pos.get('quantity', 0))
            
            # SELECTIVE PENCE TO POUNDS
            # UK stocks (.L) are in Pence. US stocks are already in Pounds.
            raw_cur_price = parse_float(pos.get('currentPrice', 0))
            raw_avg_price = parse_float(pos.get('averagePrice', 0))
            
            # IMPROVED UK DETECTION: .L or specifically _GB_
            # US stocks often have _US_EQ, so we must be specific.
            is_uk = (raw_ticker.endswith('.L') or '_GB_' in raw_ticker) and '_US_' not in raw_ticker
            
            if is_uk:
                cur_price = raw_cur_price / 100.0
                avg_price = raw_avg_price / 100.0
            else:
                # Target US/Global stocks are already in base currency (Pounds)
                cur_price = raw_cur_price
                avg_price = raw_avg_price
            
            invested = qty * avg_price
            market_val = qty * cur_price
            # total_value is derived from account 'total', we don't increment here 
            # to avoid double counting, unless account total is missing.
            
            # 3. The Yield Calculation (Simulated)
            raw_yield_mock = (hash(ticker) % 400) / 10000.0 + 0.01 
            
            # 4. The Tax Reality
            is_us = currency == 'USD' or '_US_' in raw_ticker
            tax_drag = US_WHT if is_us else 0.0
            net_yield = raw_yield_mock * (1 - tax_drag)
            
            # 5. The Verdict
            pnl_pct = ((market_val - invested) / invested) if invested > 0 else 0
            
            pass_hurdle = False
            logic_note = ""
            
            if net_yield > RISK_FREE_RATE:
                pass_hurdle = True
                logic_note = "Yields > Cash"
            elif (net_yield + pnl_pct) > MIN_HURDLE:
                 pass_hurdle = True
                 logic_note = "Growth compensated"
            else:
                 pass_hurdle = False
                 logic_note = f"Fails Cash Hurdle ({RISK_FREE_RATE*100:.1f}%)"

            architect_audit.append({
                'ticker': ticker,
                'weight': "N/A", 
                'pnl_pct': f"{pnl_pct*100:+.1f}%",
                'net_yield': f"{net_yield*100:.2f}%",
                'is_us': is_us,
                'verdict': "PASS" if pass_hurdle else "FAIL",
                'action': "HOLD" if pass_hurdle else "TRIM",
                'logic': logic_note
            })

            # --- HEATMAP POPULATION (RESTORED) ---
            heatmap_data.append({
                'x': ticker,
                'y': market_val,
                'fillColor': '#28a745' if pnl_pct >= 0 else '#dc3545',
                'custom_main': f"£{market_val:,.2f}",
                'custom_sub': f"{pnl_pct*100:+.1f}%"
            })

        architect_audit.sort(key=lambda x: x['verdict'] == 'PASS') 
        
    except Exception as e:
        import traceback
        print("!!! CRASH REPORT (T212 Connection) !!!")
        traceback.print_exc()
        print(f"Error: {e}")
        # Capture FULL traceback
        t212_error = f"{str(e)} | {traceback.format_exc().splitlines()[-1]}"
    
    # --- INTELLIGENCE ENGINE (PHASE 2 - ALWAYS RUN) ---
    try:
        import fetch_intelligence
        server_intelligence = fetch_intelligence.run_intel()
        
        # --- GHOST PROTOCOL (PHASE 4) ---
        # Merge Offline Assets (Gold, Cash, etc.)
        ghosts = server_intelligence.get('ghost_holdings', [])
        if ghosts:
             print(f"Ghost Protocol: Merging {len(ghosts)} offline assets...")
             for g in ghosts:
                 g_name = g.get('name', 'Unknown Asset')
                 g_val = float(g.get('value', 0.0))
                 total_value += g_val
                 
                 # Exclude Cash from Heatmap
                 if "CASH" not in g_name.upper():
                     heatmap_data.append({
                        'x': g_name,
                        'y': g_val,
                        'fillColor': '#6c757d', # Grey for Ghost/Neutral
                        'custom_main': f"£{g_val:,.2f}",
                        'custom_sub': "OFFLINE"
                     })
                 
    except Exception as e:
        print(f"INTEL FAILURE: {e}")
        server_intelligence = {"watchlist": [], "sitrep": {
            "type": "SYSTEM FAILURE",
            "context": "Offline Mode",
            "timestamp": datetime.utcnow().strftime("%H:%M UTC"),
            "headline": "INTELLIGENCE ENGINE OFFLINE",
            "body": "Unable to connect to market data feeds. Check API logs.",
            "status_color": "text-rose-500"
        }}

    # --- STATUS REPORT LOGIC ---
    if t212_error:
        system_status = "ERROR"
        status_sub = t212_error
        status_color = "text-rose-500"
    else:
        system_status = "ONLINE"
        status_sub = f"Synced: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
        status_color = "text-emerald-500"

    # 3. GENERATE HTML (Fail Safe)
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        template_str = f.read()

    from jinja2 import Template
    template = Template(template_str)
    
    html_output = template.render(
        total_value=f"£{total_value:,.2f}", 
        cash_reserves=f"£{cash_reserves:,.2f}",
        projected_income=f"£{projected_income:,.2f}", 
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        total_fees_str=total_fees_str,
        # System Status Injection
        system_status=system_status,
        status_sub=status_sub,
        status_color=status_color,
        # Datasets
        heatmap_dataset=json.dumps(heatmap_data),
        # Architect Data
        moat_audit=architect_audit,
        # Intelligence Data
        recon_data=server_intelligence.get('watchlist', []),
        sitrep=server_intelligence.get('sitrep', {
            "type": "SYSTEM WAITING",
            "context": "Initializing...",
            "timestamp": datetime.now().strftime("%H:%M UTC"),
            "headline": "AWAITING INTELLIGENCE",
            "body": "System is coming online. Please wait.",
            "status_color": "text-neutral-500"
        }),
        portfolio_json='[]' 
    )
    
    with open('index.html', 'w', encoding='utf-8') as f: 
        f.write(html_output)
        
    print("Build Complete (Intelligence Mode). v2.0 Ready.")

if __name__ == "__main__":
    main()
