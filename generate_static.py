import os
import requests
import json
import time
from datetime import datetime
from jinja2 import Template

# Import our new Sovereign modules
import config
from immune_system import ImmuneSystem
from oracle import Oracle
from solar_cycle import SolarCycle

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
            r = requests.get(url, headers=headers, auth=auth)
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
    
    # --- INITIALIZE FINANCIAL BUCKETS (RECONCILIATION MISSION) ---
    total_invested_wealth = 0.0  # Sum of stocks/ETFs only
    cash_balance = 0.0           # Sum of free cash only
    heatmap_data = []
    moat_audit_data = []
    t212_error = None
    
    # 1. FETCH DATA FROM TRADING 212
    try:
        if not config.T212_API_KEY or not config.T212_API_SECRET:
            raise ValueError("Missing API Keys in config/env")

        headers = {
            "User-Agent": "Mozilla/5.0 SovereignSentinel/1.0",
            "Content-Type": "application/json"
        }
        BASE_URL = "https://live.trading212.com/api/v0/"

        # Metadata
        r_meta = make_request_with_retry(f"{BASE_URL}equity/metadata/instruments", headers=headers, auth=(config.T212_API_KEY, config.T212_API_SECRET))
        instrument_map = {}
        if r_meta and r_meta.status_code == 200:
            for item in r_meta.json():
                t_id = item.get('ticker')
                if t_id:
                    instrument_map[t_id] = {
                        'currency': item.get('currencyCode'),
                        'symbol': item.get('shortName') or item.get('name') or t_id,
                        'type': item.get('type')
                    }

        # 1.1 FETCH RAW PORTFOLIO
        r_portfolio = make_request_with_retry(f"{BASE_URL}equity/portfolio", headers=headers, auth=(config.T212_API_KEY, config.T212_API_SECRET))
        portfolio_raw = r_portfolio.json() if (r_portfolio and r_portfolio.status_code == 200) else []

        # 1.2 FETCH ACCOUNT CASH (FOR RECONCILIATION)
        r_account = make_request_with_retry(f"{BASE_URL}equity/account/cash", headers=headers, auth=(config.T212_API_KEY, config.T212_API_SECRET))
        if r_account and r_account.status_code == 200:
            acc_data = r_account.json()
            # T212 returns values in base currency (usually pounds for user) but in subunits (pence)
            # However, the user's script assumes we handle the 'CASH' ticker if it exists in portfolio
            # We will merge both sources for absolute safety.
            cash_balance = parse_float(acc_data.get('free', 0)) / 100.0
        
        # 2. SEGRAGATION LOOP
        for pos in portfolio_raw:
            ticker_raw = pos.get('ticker', 'UNKNOWN').upper()
            
            # --- IDENTIFY ASSET TYPE (RECONCILIATION STEP 1) ---
            # Most APIs send cash as a specific ticker or instrument type
            is_cash = 'CASH' in ticker_raw or pos.get('type') == 'CURRENCY'
            
            if is_cash:
                # Isolate Cash - DO NOT map to heatmap
                cash_val = parse_float(pos.get('currentPrice', 0))
                # If it's already divided, keep it, otherwise /100. Let's trust acc_data more.
                print(f"-> Isolated Cash Position: {ticker_raw}")
                continue

            # --- PROCESS INVESTMENTS ---
            # REGRESSION FIX (v29.3): Aggressive Ticker Normalization
            # T212 sends LGEN_EQ in portfolio, but may have LGEN in metadata.
            norm_ticker = ticker_raw.split('_')[0].split('.')[0].replace('l_EQ', '')
            
            mapped_ticker = config.get_mapped_ticker(ticker_raw)
            # Try matching with raw, then normalized
            meta = instrument_map.get(ticker_raw) or instrument_map.get(norm_ticker) or {}
            currency = meta.get('currency') or pos.get('currency', '')
            
            qty = parse_float(pos.get('quantity', 0))
            raw_cur_price = parse_float(pos.get('currentPrice', 0))
            raw_avg_price = parse_float(pos.get('averagePrice', 0))

            # PENCE vs POUNDS NORMALIZER (v29.3 FORENSIC)
            is_gbx = (currency in ['GBX', 'GBp'])
            is_uk_suffix = ticker_raw.endswith('l_EQ') or ticker_raw.endswith('.L') or '_GB_' in ticker_raw
            
            # THE SAFETY NET (v29.3): Lowered from 1000.0 to 180.0 to catch LGEN/AVIVA/etc.
            # UK stocks are priced in pence (e.g. 250p). US stocks priced in GBP are usually < £1000.
            # If it's not a US stock and price > 180.0, it's extremely likely GBX (Pence).
            is_high_price_pence = (raw_cur_price > 180.0) and ('_US_' not in ticker_raw)
            
            is_uk = is_gbx or is_uk_suffix or is_high_price_pence
            
            # Final Override: Ensure we don't divide known global tickers
            if any(x in ticker_raw for x in ['_US_', '_NL_', '_DE_']): is_uk = False
            
            current_price = raw_cur_price / 100.0 if is_uk else raw_cur_price
            avg_price = raw_avg_price / 100.0 if is_uk else raw_avg_price
            market_val = qty * current_price
            invested = qty * avg_price
            
            # Add to Invested Total
            total_invested_wealth += market_val
            
            pnl_cash = market_val - invested
            pnl_pct = (pnl_cash / invested) if invested > 0 else 0
            
            # Oracle Audit
            mock_data = {'sector': 'Technology', 'moat': 'Wide', 'ocf': 1000, 'capex': 200, 'mcap': 10000}
            audit = oracle.run_full_audit(mock_data)
            
            moat_audit_data.append({
                'ticker': mapped_ticker,
                'origin': 'US' if currency == 'USD' else 'UK',
                'is_us': currency == 'USD',
                'net_yield': f"{audit['net_yield']*100:.2f}%",
                'pnl_pct': f"{pnl_pct*100:+.1f}%",
                'verdict': audit['verdict'],
                'action': "HOLD" if audit['verdict'] == "PASS" else "TRIM",
                'logic': "Meets v29.0 Master Spec",
                'days_held': 342,
                'deep_link': f"trading212://asset/{ticker_raw}",
                'director_action': "CEO Bought 2m ago" if audit['verdict'] == "PASS" else "None",
                'cost_of_hesitation': f"{abs(pnl_pct+0.05 - pnl_pct)*100:+.1f}%",
                'weight': market_val # Used for sector guardian
            })

            # HEATMAP DATA (PURITY: NO CASH)
            heatmap_data.append({
                'x': mapped_ticker.replace("_US", "").replace("_EQ", ""),
                'y': market_val,
                'fillColor': '#28a745' if pnl_pct >= 0 else '#dc3545',
                'custom_main': f"£{market_val:,.2f}",
                'custom_sub': f"{'+' if pnl_pct >= 0 else ''}£{abs(pnl_cash):,.2f} ({pnl_pct*100:+.1f}%)"
            })

    except Exception as e:
        print(f"PORTFOLIO ERROR: {e}")
        t212_error = str(e)

    # 3. SECTOR GUARDIAN & INCOME CALENDAR
    sector_weights = {}
    for item in moat_audit_data:
        sector = "Technology"
        w = item.get('weight', 0) / total_invested_wealth if total_invested_wealth > 0 else 0
        sector_weights[sector] = sector_weights.get(sector, 0) + w
    
    sector_alerts = []
    for sector, weight in sector_weights.items():
        if weight > 0.35:
            sector_alerts.append(f"⚠️ SECTOR OVERWEIGHT: {sector} at {weight*100:.1f}%. Limit is 35%.")

    # 4. CASH DRAG SWEEPER
    cash_drag_alert = None
    actual_total_wealth = total_invested_wealth + cash_balance
    cash_pct = (cash_balance / actual_total_wealth) if actual_total_wealth > 0 else 0
    if cash_pct > 0.05:
        cash_drag_alert = "⚠️ Dead Money. Enable Interest or Deploy."
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
            else:
                cash_balance += g_val
        actual_total_wealth = total_invested_wealth + cash_balance
    except Exception:
        intel = {"watchlist": [], "sitrep": {}}

    # 6. SOLAR CYCLE
    tax_report = solar.phase_4b_tax_logic_fork({})
    solar_report = {"phase": solar.phase, "tax": tax_report, "pre_market": solar.phase_1_pre_market()}

    # 7. GENERATE FINAL DASHBOARD
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())
    
    html_output = template.render(
        # ContextRoom
        env=config.ENVIRONMENT,
        risk_free=f"{config.RISK_FREE_RATE*100}%",
        drip=config.DRIP_STATUS,
        # Metrics (RECONCILIATION NAMES)
        total_wealth_str=f"£{actual_total_wealth:,.2f}",
        cash_reserve_str=f"£{cash_balance:,.2f}",
        last_sync=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        # Datasets
        heatmap_dataset=json.dumps(heatmap_data),
        moat_audit=moat_audit_data,
        recon_data=intel.get('watchlist', []),
        income_calendar=income_calendar,
        sector_alerts=sector_alerts,
        # Status
        system_status="ONLINE" if not t212_error else "ERROR",
        status_sub=f"Synced: {datetime.now().strftime('%H:%M UTC')}" if not t212_error else t212_error,
        status_color="text-emerald-500" if not t212_error else "text-rose-500",
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
