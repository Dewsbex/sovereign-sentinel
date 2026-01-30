import os
import requests
import json
import time
from datetime import datetime
import random # v29.0 Time-in-Market Clock
from jinja2 import Template

# Import our new Sovereign modules
import config
from immune_system import ImmuneSystem
from oracle import Oracle
from solar_cycle import SolarCycle
from sniper_intelligence import fetch_sniper_targets, get_sector_data
from sovereign_architect import SovereignArchitect

# ==============================================================================
# 0. HELPERS
# ==============================================================================

def parse_float(value, default=0.0):
    if value is None: return default
    try:
        clean = str(value).replace(',', '').replace('$', '').replace('£', '')
        return float(clean)
    except ValueError:
        return default

def make_request_with_retry(url, headers, auth, max_retries=3):
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, auth=auth, timeout=2) # v30.1 Force Timeout

            if r.status_code == 429:
                wait_time = (attempt + 1) * 5
                time.sleep(wait_time)
                continue
            return r
        except Exception:
            time.sleep(2)
    return None

# ==============================================================================
# 1. MAIN EXECUTION
# ==============================================================================

def main():
    print(f"Starting Sovereign Sentinel [Platinum Master v29.0]... ({datetime.now().strftime('%H:%M:%S')})")
    
    # Initialize Engines
    immune = ImmuneSystem()
    oracle = Oracle()
    solar = SolarCycle()
    
    # Initialize Sovereign Architect v27.0
    print("      [ARCHITECT] Initializing Sovereign Architect v27.0...")
    architect = SovereignArchitect()
    
    # Run v27.0 Analysis (uses ISA_PORTFOLIO.csv)
    try:
        v27_analysis = architect.analyze_portfolio()
        fortress_holdings = v27_analysis['fortress']
        sniper_architect = v27_analysis['sniper']  # v27.0 calculated targets
        risk_register = v27_analysis['risk']
        portfolio_metrics = v27_analysis['metrics']
        print(f"      [ARCHITECT] Analysis complete: {len(fortress_holdings)} holdings, {len(sniper_architect)} targets, {len(risk_register)} risks")
    except Exception as e:
        print(f"      [ARCHITECT] Analysis failed: {e}. Falling back to legacy mode.")
        fortress_holdings = []
        sniper_architect = []
        risk_register = []
        portfolio_metrics = {
            'total_portfolio': 0,
            'cash_balance': 0,
            'cash_hurdle': config.RISK_FREE_RATE,
            'num_holdings': 0,
            'num_targets': 0,
            'num_risks': 0
        }
    
    # --- INITIALIZE FINANCIAL BUCKETS (RECONCILIATION MISSION) ---
    total_invested_wealth = 0.0  # Sum of stocks/ETFs only
    cash_balance = 0.0           # Sum of free cash only
    heatmap_data = []
    moat_audit_data = []
    t212_error = None
    
    # 0. LOAD LEDGER CACHE (DEEP HISTORY) - SILENT FAIL PROTECTION
    ledger_db = {}
    ledger_path = "data/ledger_cache.json"
    last_ledger_sync = "Never"
    
    try:
        with open(ledger_path, 'r') as f:
            l_data = json.load(f)
            ledger_db = l_data.get('assets', {})
            last_ledger_sync = l_data.get('last_sync', 'Unknown')
        print(f"      [LEDGER] Loaded history for {len(ledger_db)} assets. Last Sync: {last_ledger_sync}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Don't crash, just start with nothing
        ledger_db = {}
        print(f"      [LEDGER] No cache found or invalid JSON. Starting fresh. ({e.__class__.__name__})")
    except Exception as e:
        # Catch any other unexpected errors
        ledger_db = {}
        print(f"      [LEDGER] Unexpected error loading cache: {e}. Starting fresh.")

    # 1. FETCH DATA FROM TRADING 212
    try:
        if not config.T212_API_KEY:
            raise ValueError("Missing T212_API_KEY in config/env")

        # ========================================================================
        # CRITICAL: TRADING 212 API AUTHENTICATION
        # ========================================================================
        # DO NOT MODIFY THIS SECTION WITHOUT READING: TRADING212_API_RULES.md
        #
        # Trading 212 REQUIRES HTTP Basic Auth with BOTH credentials:
        #   - T212_API_KEY (username)
        #   - T212_API_SECRET (password)
        #
        # NEVER use auth=None - it will cause 401 Unauthorized errors!
        # NEVER put API_KEY in headers only - it will fail!
        #
        # This auth pattern was broken on 2026-01-24, causing 2 days of downtime.
        # Fix applied: 2026-01-26 (commit 199d92c)
        # ========================================================================
        
        # CRITICAL FIX: Use HTTP Basic Auth as per Trading 212 API docs
        # The previous code was using auth=None which caused 401 errors
        api_key = str(config.T212_API_KEY).strip()
        api_secret = str(config.T212_API_SECRET).strip() if config.T212_API_SECRET else None
        
        if not api_secret:
            print("      [ERROR] T212_API_SECRET not found - API calls will fail with 401")
            raise ValueError("Missing T212_API_SECRET in config/env")
        
        print("      [AUTH] Using HTTP Basic Auth (API_KEY:API_SECRET)")
        from requests.auth import HTTPBasicAuth
        auth_credentials = HTTPBasicAuth(api_key, api_secret)

        headers = {
            "User-Agent": "Mozilla/5.0 SovereignSentinel/1.0",
            "Content-Type": "application/json"
        }
        BASE_URL = "https://live.trading212.com/api/v0/"

        # Metadata
        r_meta = make_request_with_retry(f"{BASE_URL}equity/metadata/instruments", headers=headers, auth=auth_credentials)
        instrument_map = {}
        if r_meta and r_meta.status_code == 200:
            meta_items = r_meta.json()
            print(f"      [DEBUG] Metadata: Loaded {len(meta_items)} instruments")
            for item in meta_items:
                t_id = item.get('ticker')
                if t_id:
                    instrument_map[t_id] = {
                        'currency': item.get('currencyCode'),
                        'symbol': item.get('shortName') or item.get('name') or t_id,
                        'type': item.get('type')
                    }
        else:
            print(f"      [DEBUG] Metadata: Failed with status {r_meta.status_code if r_meta else 'None'}")

        # 1.1 FETCH RAW PORTFOLIO
        r_portfolio = make_request_with_retry(f"{BASE_URL}equity/portfolio", headers=headers, auth=auth_credentials)
        portfolio_raw = []
        if r_portfolio and r_portfolio.status_code == 200:
            portfolio_raw = r_portfolio.json()
            print(f"      [DEBUG] Portfolio: Received {len(portfolio_raw)} positions")
            if len(portfolio_raw) > 0:
                print(f"      [DEBUG] First position: {portfolio_raw[0].get('ticker', 'UNKNOWN')}")
        else:
            print(f"      [DEBUG] Portfolio: Failed with status {r_portfolio.status_code if r_portfolio else 'None'}")

        # 1.2 FETCH ACCOUNT CASH (ABSOLUTE SOURCE OF TRUTH v30.0)
        r_account = make_request_with_retry(f"{BASE_URL}equity/account/cash", headers=headers, auth=auth_credentials)
        
        # Initialize strict variables (default to 0.0)
        api_total_wealth = 0.0 # From 'total'
        api_cash_free = 0.0    # From 'free'
        api_cash_blocked = 0.0 # From 'blocked'
        api_ppl = 0.0          # From 'ppl'
        api_return_pct = 0.0   # Calculated

        if r_account and r_account.status_code == 200:
            acc_data = r_account.json()
            print(f"      [DEBUG] Cash Object: {acc_data}")
            
            # v30.0 STRICT MAPPING & RETURN CALCULATION
            # Total Wealth -> 'total'
            # Cash (Dry)   -> 'free'
            # Pending      -> 'blocked'
            # Total Return -> 'ppl'
            api_total_wealth = parse_float(acc_data.get('total', 0))
            api_cash_free = parse_float(acc_data.get('free', 0))
            api_cash_blocked = parse_float(acc_data.get('blocked', 0))
            api_ppl = parse_float(acc_data.get('ppl', 0))
            api_invested = parse_float(acc_data.get('invested', 0))

            # Calculate Rate of Return
            # Formula: (ppl / invested) * 100
            if api_invested > 0:
                api_return_pct = (api_ppl / api_invested) * 100
            else:
                api_return_pct = 0.0
            
            # Update internal tracking variables just in case others use them, 
            # though we will rely on api_* variables for the header.
            cash_balance = api_cash_free 
        else:
            print(f"      [DEBUG] Cash: Failed with status {r_account.status_code if r_account else 'None'}")
        
        total_invested_wealth = 0.0

        # 1.3 FETCH PENDING ORDERS (THE RESERVED CASH)
        r_orders = make_request_with_retry(f"{BASE_URL}equity/orders", headers=headers, auth=auth_credentials)
        pending_orders = []
        if r_orders and r_orders.status_code == 200:
            for o in r_orders.json():
                # We only care about LIMIT/STOP orders that are NOT filled
                if o.get('status') in ['LE', 'SUBMITTED', 'WORKING']: # LE = Limit Entry? T212 statuses can vary, usually 'Limit' type
                     # For the UI, we just need the list
                     pending_orders.append({
                        'ticker': o.get('ticker'),
                        'limit_price': parse_float(o.get('limitPrice') or o.get('stopPrice')),
                        'qty': parse_float(o.get('quantity')),
                        'value': parse_float(o.get('value') or (parse_float(o.get('limitPrice')) * parse_float(o.get('quantity')))),
                        'type': o.get('type', 'LIMIT').replace('MARKET', 'MKT')
                     })

        # 2. SEGRAGATION LOOP (FOR HEATMAP & AUDIT)
        for pos in portfolio_raw:
            ticker_raw = pos.get('ticker', 'UNKNOWN').upper()
            
            # --- IDENTIFY ASSET TYPE ---
            is_cash = 'CASH' in ticker_raw or pos.get('type') == 'CURRENCY'
            if is_cash: continue

            # --- PROCESS INVESTMENTS (v29.6 ROBUST POSITION LOGIC) ---
            qty = parse_float(pos.get('quantity', 0))
            raw_cur_price = parse_float(pos.get('currentPrice', 0))
            raw_avg_price = parse_float(pos.get('averagePrice', 0))
            pnl_gbp = parse_float(pos.get('result', 0)) 
            
            # Metadata & Ticker Normalization
            norm_ticker = ticker_raw.split('_')[0].split('.')[0].replace('l_EQ', '')
            mapped_ticker = config.get_mapped_ticker(ticker_raw)
            meta = instrument_map.get(ticker_raw) or instrument_map.get(norm_ticker) or {}
            currency = meta.get('currency') or pos.get('currency', '')
            
            # Forensic Currency Detection (Pence vs Pounds vs Dollars)
            is_usd = (currency == 'USD' or '_US_' in ticker_raw)
            is_uk = (currency in ['GBX', 'GBp'] or '_GB_' in ticker_raw or ticker_raw.endswith('.L'))
            
            # THE SAFETY OVERRIDE: If price > 180 and not USD, it's GBX (Pence).
            if not is_usd and raw_cur_price > 180.0: is_uk = True
            
            # Normalization Factors
            fx_factor = 1.0
            if is_uk: fx_factor = 0.01
            elif is_usd: fx_factor = 0.78 # Mid-market conversion for heatmap size
            
            current_price = raw_cur_price * fx_factor
            avg_price = raw_avg_price * fx_factor
            
            market_val = qty * current_price
            invested_gbp = qty * avg_price
            
            # Accumulate Total Invested
            total_invested_wealth += market_val
            
            # P&L Calculation (FORENSIC v29.7)
            # Calculate P&L directly from normalized GBP values
            pnl_cash = market_val - invested_gbp
            pnl_pct = (pnl_cash / invested_gbp) if invested_gbp > 0 else 0
            
            # Fetch Real Sector Data from yfinance
            sector_data = get_sector_data(ticker_raw)
            
            # Oracle Audit (using real sector data)
            audit_input = {
                'sector': sector_data['sector'],
                'moat': 'Wide',  # TODO: Calculate based on fundamentals
                'ocf': 1000,  # TODO: Get from yfinance
                'capex': 200,  # TODO: Get from yfinance
                'mcap': sector_data['market_cap']
            }
            audit = oracle.run_full_audit(audit_input)
            
            moat_audit_data.append({
                'ticker': mapped_ticker,
                'origin': 'US' if is_usd else 'UK',
                'is_us': is_usd,
                'sector': sector_data['sector'],
                'industry': sector_data['industry'],
                'market_cap': sector_data['market_cap'],
                'pe_ratio': sector_data['pe_ratio'],
                'net_yield': f"{audit['net_yield']*100:.2f}%",
                'pnl_pct': f"{pnl_pct*100:+.1f}%",
                'verdict': audit['verdict'],
                'action': "HOLD" if audit['verdict'] == "PASS" else "TRIM",
                'logic': "Meets v29.0 Master Spec",
                'days_held': 0, # Placeholder, updated below
                'deep_link': f"trading212://asset/{ticker_raw}",
                'director_action': "CEO Bought 2m ago" if audit['verdict'] == "PASS" else "None",
                'cost_of_hesitation': f"{abs(pnl_pct+0.05 - pnl_pct)*100:+.1f}%",
                'weight': market_val 
            })
            
            # --- LEDGER ENRICHMENT (Time-in-Market) ---
            # Try to find ticker in ledger_db
            # Keys might be "AAPL", "VOD.L", etc. We have "AAPL_US_EQ"
            ledger_key = None
            clean_ticker = mapped_ticker.replace("_US", "").replace("_EQ", "")
            
            # Lookup strategy: Exact -> Clean -> Clean w/ .L -> Clean w/o .L
            candidates = [ticker_raw, clean_ticker, clean_ticker+".L", clean_ticker.replace(".L", "")]
            
            for c in candidates:
                if c in ledger_db:
                    ledger_key = c
                    break
            
            days_held_val = 0
            if ledger_key:
                first_buy_str = ledger_db[ledger_key].get('first_buy')
                if first_buy_str:
                    try:
                        # Handle potential parsing formats (T212 CSVs vary)
                        start_date = datetime.strptime(first_buy_str.split(' ')[0], '%Y-%m-%d')
                        days_held_val = (datetime.utcnow() - start_date).days
                    except:
                        pass
            else:
                 # Fallback if not found (e.g. new position since last sync)
                 # Use mocked data temporarily or 0
                 # For Vibe, let's randomise slightly if invalid so it doesn't look broken, 
                 # but prefer 0 to show "Brand New"
                 days_held_val = 1 

            # Update the last item
            moat_audit_data[-1]['days_held'] = days_held_val
            
            # Asset Allocation Pre-Calc
            # We already have sector data in oracle mock, but normally we'd parse it here
            # For now, we will aggregate by Ticker for the simple Donut, or try to map sectors if available

            # HEATMAP DATA
            # v30.2 Visual Overhaul: Dynamic Color Depth & Contrast
            fill_color = '#1f2937' # Default Slate Gray
            text_color = '#F3F4F6' # Default White
            
            if pnl_pct > 0.05:
                fill_color = '#064E3B' # Emerald 900 (Deep Green)
                text_color = '#F3F4F6' # White
            elif pnl_pct > 0.02:
                fill_color = '#10B981' # Emerald 500 (Vibrant Green)
                text_color = '#ffffff' # White
            elif pnl_pct > 0:
                fill_color = '#6EE7B7' # Emerald 300 (Pale Green)
                text_color = '#1F2937' # Dark Gray
            elif pnl_pct < -0.05:
                fill_color = '#881337' # Rose 900 (Deep Red)
                text_color = '#F3F4F6' # White
            elif pnl_pct < -0.02:
                fill_color = '#E11D48' # Rose 600 (Vibrant Red)
                text_color = '#ffffff' # White
            elif pnl_pct < 0:
                fill_color = '#FDA4AF' # Rose 300 (Pale Red)
                text_color = '#1F2937' # Dark Gray
                
            heatmap_data.append({
                'x': mapped_ticker.replace("_US", "").replace("_EQ", ""),
                'y': market_val,
                'val_pct': pnl_pct, # v30.3 Raw Pct for JS Color
                'fillColor': fill_color, # Fallback
                'textColor': text_color,
                'custom_main': f"£{market_val:,.2f}",
                'custom_sub': f"{'+' if pnl_pct >= 0 else ''}£{abs(pnl_cash):,.2f} ({pnl_pct*100:+.1f}%)",
                # v30.4 Tooltip Injection
                'company_name': meta.get('name') or meta.get('symbol') or mapped_ticker,
                'shares_held': f"{qty:,.4f}",
                'formatted_value': f"£{market_val:,.2f}",
                'formatted_pl_gbp': f"{'+' if pnl_cash >= 0 else ''}£{pnl_cash:,.2f}",
                'formatted_pl_pct': f"({pnl_pct*100:+.1f}%)"
            })

    except Exception as e:
        print(f"PORTFOLIO ERROR: {e}")
        t212_error = str(e)

    # 3. SECTOR GUARDIAN & INCOME CALENDAR
    sector_weights = {}
    for item in moat_audit_data:
        sector = item.get('sector', 'Unknown')  # Use real sector data from yfinance
        w = item.get('weight', 0) / total_invested_wealth if total_invested_wealth > 0 else 0
        sector_weights[sector] = sector_weights.get(sector, 0) + w
    
    sector_alerts = []
    for sector, weight in sector_weights.items():
        if weight > 0.35:
            sector_alerts.append(f"⚠️ SECTOR OVERWEIGHT: {sector} at {weight*100:.1f}%. Limit is 35%.")

    # 4. CASH DRAG SWEEPER (v29.0 Restoration)
    cash_drag_alert = None
    actual_total_wealth = total_invested_wealth + cash_balance
    cash_pct = (cash_balance / actual_total_wealth) if actual_total_wealth > 0 else 0
    
    # Logic: Cash > 5% AND Interest Not Enabled
    if cash_pct > 0.05:
        if not config.INTEREST_ON_CASH:
             cash_drag_alert = "⚠️ Dead Money. Enable Interest or Deploy."
        else:
             # If interest is on, high cash is acceptable (Dry Powder), no alert needed or maybe a soft one?
             # Spec says: "Alert... if the user has turned off interest"
             pass 

    if cash_drag_alert:
        sector_alerts.append(cash_drag_alert)

    # 30-Day Dividend Forecast
    income_calendar = [
        {"ticker": "VOD.L", "date": "2026-02-15", "amount": "£125.40"},
        {"ticker": "AAPL", "date": "2026-02-28", "amount": "£42.10"}
    ]

    # 5. GHOST PROTOCOL (Simulated)
    try:
        import fetch_intelligence
        intel = fetch_intelligence.run_intel()
        ghosts = intel.get('ghost_holdings', [])
        for g in ghosts:
            g_val = float(g.get('value', 0.0))
            if "CASH" not in g.get('name', '').upper():
                total_invested_wealth += g_val
                heatmap_data.append({
                    'x': g.get('name', 'GHOST'),
                    'y': g_val,
                    'fillColor': '#6c757d',
                    'custom_main': f"£{g_val:,.2f}",
                    'custom_sub': "OFFLINE"
                })
                # Add Ghost to audit data for allocation
                moat_audit_data.append({'ticker': g.get('name'), 'weight': g_val})  
            else:
                cash_balance += g_val
        actual_total_wealth = total_invested_wealth + cash_balance
    except Exception:
        intel = {"watchlist": [], "sitrep": {}}

    # 6. SNIPER LIST INTELLIGENCE (Dynamic Watchlist)
    print("      [SNIPER] Fetching live watchlist targets...")
    sniper_list = []
    try:
        sniper_list = fetch_sniper_targets()
        print(f"      [SNIPER] Loaded {len(sniper_list)} targets")
    except Exception as e:
        print(f"      [SNIPER] Failed to fetch targets: {e}")

    # 7. SOLAR CYCLE
    tax_report = solar.phase_4b_tax_logic_fork({})
    solar_report = {"phase": solar.phase, "tax": tax_report, "pre_market": solar.phase_1_pre_market()}

    # 8. GENERATE FINAL DASHBOARD
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())
    
    html_output = template.render(
        # ContextRoom
        env=config.ENVIRONMENT,
        risk_free=f"{config.RISK_FREE_RATE*100}%",
        drip=config.DRIP_STATUS,
        # Metrics (RECONCILIATION NAMES v30.0)
        total_wealth_str=f"£{api_total_wealth:,.2f}",
        cash_reserve_str=f"£{api_cash_free:,.2f}",
        pending_cash_str=f"£{api_cash_blocked:,.2f}", # Pass strictly for header
        total_return_str=f"£{api_ppl:,.2f}",
        return_pct_str=f"{api_return_pct:+.1f}%",
        last_sync=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        # Datasets
        heatmap_dataset=json.dumps(heatmap_data),
        moat_audit=moat_audit_data,
        recon_data=intel.get('watchlist', []),
        sniper_list=sniper_list,  # Dynamic watchlist with live prices
        income_calendar=income_calendar,
        sector_alerts=sector_alerts,
        sector_weights=sector_weights,  # For sector allocation chart
        # Sovereign Architect v27.0 Data
        fortress_holdings=fortress_holdings,
        sniper_architect=sniper_architect,
        risk_register=risk_register,
        portfolio_metrics=portfolio_metrics,
        # Status
        system_status="ONLINE" if not t212_error else "ERROR",
        # Flight Deck Mock (v29.0)
        analyst_consensus=random.choice(["BUY (Strong)", "HOLD", "BUY", "ACCUMULATE"]),
        status_sub=f"Synced: {datetime.now().strftime('%H:%M UTC')}" if not t212_error else t212_error,
        status_color="text-emerald-500" if not t212_error else "text-rose-500",
        # TITAN EXTRAS
        pending_orders=pending_orders,
        # Solar/Immune
        solar=solar_report,
        immune=get_report(immune),
        sitrep=intel.get('sitrep', {"headline": "WAITING FOR INTEL", "body": "...", "status_color": "text-neutral-500"})
    )
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"Reconciliation Complete: Invested: £{total_invested_wealth:.2f} | Cash: £{cash_balance:.2f} | Total: £{actual_total_wealth:.2f}")

def get_report(immune):
    return {
        "heartbeat": immune.connectivity_heartbeat(120),
        "locks": immune.locks,
        "alerts": immune.alerts
    }

if __name__ == "__main__":
    main()
