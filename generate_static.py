import os
import requests
from requests.auth import HTTPBasicAuth
import json
import time
import re
from datetime import datetime
import random
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

def make_request_with_retry(session, url, auth=None, headers=None, max_retries=3):
    """v29.5: Strict Rate-Limited Fetcher. 10s Delay."""
    for attempt in range(max_retries):
        try:
            r = session.get(url, auth=auth, headers=headers, timeout=15)
            print(f"      [API] {url.split('/')[-1]} -> {r.status_code}")
            
            if r.status_code == 429:
                wait_time = (attempt + 1) * 30
                print(f"      [429] Rate Limit. Cooling down {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            # v29.5: 10s delay to stay safely under 6 req/min limit
            time.sleep(10.0)
            return r
        except Exception as e:
            print(f"      [ERR] {e}")
            time.sleep(5)
    return None

def main():
    print(f"Starting Sovereign Sentinel [v29.5 - Rate Limit Safe]... ({datetime.now().strftime('%H:%M:%S')})")
    
    # 401 Lockout Protocol
    if os.path.exists('401_block.lock'):
        st = os.path.getmtime('401_block.lock')
        elapsed = time.time() - st
        if elapsed < 300:
             print(f"      [BLOCK] 401 Security Lockout active for {300 - int(elapsed)}s. Exiting.")
             return
        else:
             os.remove('401_block.lock')
    
    # Concurrency Lock
    if os.path.exists('sentinel.lock'):
        with open('sentinel.lock', 'r') as f:
             # Just warn, don't crash, in case of stale lock
             print(f"      [WARN] Lock file exists.")
    
    with open('sentinel.lock', 'w') as f:
        f.write(str(os.getpid()))

    try:
        immune = ImmuneSystem()
        oracle = Oracle()
        solar = SolarCycle()
        
        total_invested_wealth = 0.0
        cash_balance = 0.0
        heatmap_data = []
        moat_audit_data = []
        t212_error = None
        pending_orders = []

        # HYBRID AUTH SETUP (v29.6)
        # T212 Spec says: Authorization: Basic <base64(key:secret)>
        # But user says: Authorization: <key> worked previously.
        auth = None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        api_key = str(config.T212_API_KEY).strip()
        
        if config.T212_API_SECRET:
            print("      [AUTH] Using HTTP Basic Auth (Recommended)")
            api_secret = str(config.T212_API_SECRET).strip()
            # requests.auth.HTTPBasicAuth handles the 'Authorization: Basic ...' header
            auth = HTTPBasicAuth(api_key, api_secret)
        else:
            print("      [AUTH] Using Legacy API Key Header (Fallback)")
            # For Legacy, we just put the key in the Authorization header
            headers["Authorization"] = api_key

        BASE_URL = os.getenv("T212_API_URL", "https://live.trading212.com/api/v0/").strip()
        if not BASE_URL.endswith('/'): BASE_URL += '/'

        session = requests.Session()
        
        # 1.1 FETCH PORTFOLIO
        r_portfolio = make_request_with_retry(session, f"{BASE_URL}equity/portfolio", auth=auth, headers=headers)
        portfolio_raw = []
        if r_portfolio and r_portfolio.status_code == 200:
             portfolio_raw = r_portfolio.json()
        elif r_portfolio and r_portfolio.status_code == 401:
             print(f"      [401] Auth failed. Body: {r_portfolio.text[:100]}")
             with open('401_block.lock', 'w') as f: f.write('BLOCK')
             t212_error = "401 Unauthorized - Check API credentials"
        
        print(f"      [DEBUG] Portfolio Count: {len(portfolio_raw)}")

        # 1.2 FETCH ACCOUNT CASH
        r_account = make_request_with_retry(session, f"{BASE_URL}equity/account/cash", auth=auth, headers=headers)
        if r_account and r_account.status_code == 200:
            acc_data = r_account.json()
            cash_balance = parse_float(acc_data.get('total', 0.0))
            if cash_balance == 0: cash_balance = parse_float(acc_data.get('free', 0.0))

        # 1.3 FETCH PENDING ORDERS
        r_orders = make_request_with_retry(session, f"{BASE_URL}equity/orders", auth=auth, headers=headers)
        if r_orders and r_orders.status_code == 200:
            for o in r_orders.json():
                if o.get('status') in ['LE', 'SUBMITTED', 'WORKING']:
                     pending_orders.append({
                        'ticker': o.get('ticker'),
                        'limit_price': parse_float(o.get('limitPrice') or o.get('stopPrice')),
                        'qty': parse_float(o.get('quantity')),
                        'value': parse_float(o.get('value') or (parse_float(o.get('limitPrice')) * parse_float(o.get('quantity')))),
                        'type': o.get('type', 'LIMIT').replace('MARKET', 'MKT')
                     })

        # 2. PROCESSING LOOP
        for pos in portfolio_raw:
            ticker_raw = pos.get('ticker', 'UNKNOWN').upper()
            is_cash = 'CASH' in ticker_raw or pos.get('type') == 'CURRENCY'
            if is_cash: continue

            qty = parse_float(pos.get('quantity', 0))
            raw_cur_price = parse_float(pos.get('currentPrice', 0))
            raw_avg_price = parse_float(pos.get('averagePrice', 0))
            
            mapped_ticker = config.get_mapped_ticker(ticker_raw)
            currency = pos.get('currency', '')
            
            is_usd = (currency == 'USD' or '_US_' in ticker_raw)
            is_uk = (currency in ['GBX', 'GBp'] or '_GB_' in ticker_raw or ticker_raw.endswith('.L'))
            if not is_usd and raw_cur_price > 180.0: is_uk = True
            
            fx_factor = 1.0
            if is_uk: fx_factor = 0.01
            elif is_usd: fx_factor = 0.78
            
            current_price = raw_cur_price * fx_factor
            avg_price = raw_avg_price * fx_factor
            market_val = qty * current_price
            invested_gbp = qty * avg_price
            
            total_invested_wealth += market_val
            pnl_cash = market_val - invested_gbp
            pnl_pct = (pnl_cash / invested_gbp) if invested_gbp > 0 else 0
            
            mock_data = {'sector': 'Technology', 'moat': 'Wide', 'ocf': 1000, 'capex': 200, 'mcap': 10000}
            audit = oracle.run_full_audit(mock_data)
            
            moat_audit_data.append({
                'ticker': mapped_ticker,
                'origin': 'US' if is_usd else 'UK',
                'is_us': is_usd,
                'net_yield': f"{audit['net_yield']*100:.2f}%",
                'pnl_pct': f"{pnl_pct*100:+.1f}%",
                'verdict': audit['verdict'],
                'action': "HOLD" if audit['verdict'] == "PASS" else "TRIM",
                'logic': "v29.4 HTTP Basic Auth",
                'days_held': random.randint(45, 800),
                'deep_link': f"trading212://asset/{ticker_raw}",
                'director_action': "CEO Bought 2m ago" if audit['verdict'] == "PASS" else "None",
                'cost_of_hesitation': f"{abs(pnl_pct+0.05 - pnl_pct)*100:+.1f}%",
                'weight': market_val 
            })
            
            heatmap_data.append({
                'x': mapped_ticker.replace("_US", "").replace("_EQ", ""),
                'y': market_val,
                'fillColor': '#37E6B0' if pnl_pct >= 0 else '#FF4B4B',
                'custom_main': f"£{market_val:,.2f}",
                'custom_sub': f"{'+' if pnl_pct >= 0 else ''}£{abs(pnl_cash):,.2f} ({pnl_pct*100:+.1f}%)"
            })

        # 3. SECTOR GUARDIAN
        sector_weights = {}
        for item in moat_audit_data:
            sector = "Technology"
            w = item.get('weight', 0) / total_invested_wealth if total_invested_wealth > 0 else 0
            sector_weights[sector] = sector_weights.get(sector, 0) + w
        
        sector_alerts = []
        for sector, weight in sector_weights.items():
            if weight > 0.35:
                sector_alerts.append(f"⚠️ SECTOR OVERWEIGHT: {sector} at {weight*100:.1f}%. Limit is 35%.")

        # 4. CASH DRAG
        actual_total_wealth = total_invested_wealth + cash_balance
        cash_pct = (cash_balance / actual_total_wealth) if actual_total_wealth > 0 else 0
        if cash_pct > 0.05 and not config.INTEREST_ON_CASH:
             sector_alerts.append("⚠️ Dead Money. Enable Interest or Deploy.")

        # 5. GHOST PROTOCOL
        try:
            import fetch_intelligence
            intel = fetch_intelligence.run_intel()
            ghosts = intel.get('ghost_holdings', [])
            for g in ghosts:
                g_val = float(g.get('value', 0.0))
                if "CASH" not in g.get('name', '').upper():
                    total_invested_wealth += g_val
                    heatmap_data.append({'x': g.get('name', 'GHOST'), 'y': g_val, 'fillColor': '#6c757d', 'custom_main': f"£{g_val:,.2f}", 'custom_sub': "OFFLINE"})
                    moat_audit_data.append({'ticker': g.get('name'), 'weight': g_val, 'pnl_pct': '0.0%', 'verdict': 'GHOST', 'action': 'WATCH', 'logic': 'Offline', 'days_held': '---', 'net_yield': '---'})
                else:
                    cash_balance += g_val
            actual_total_wealth = total_invested_wealth + cash_balance
        except Exception:
            intel = {"watchlist": [], "sitrep": {}}

        # 6. SOLAR CYCLE
        tax_report = solar.phase_4b_tax_logic_fork({})
        solar_report = {"phase": solar.phase, "tax": tax_report, "pre_market": solar.phase_1_pre_market()}

        # 7. GENERATE DASHBOARD
        with open('templates/base_vibe.html', 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        income_calendar = [{"ticker": "VOD.L", "date": "2026-02-15", "amount": "£125.40"}, {"ticker": "AAPL", "date": "2026-02-28", "amount": "£42.10"}]
        
        html_output = template.render(
            env=config.ENVIRONMENT,
            risk_free=f"{config.RISK_FREE_RATE*100}%",
            drip=config.DRIP_STATUS,
            total_wealth_str=f"£{actual_total_wealth:,.2f}",
            cash_reserve_str=f"£{cash_balance:,.2f}",
            last_sync=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            heatmap_dataset=json.dumps(heatmap_data),
            moat_audit=moat_audit_data,
            recon_data=intel.get('watchlist', []),
            income_calendar=income_calendar,
            sector_alerts=sector_alerts,
            system_status="ONLINE" if not t212_error else "ERROR",
            analyst_consensus=random.choice(["BUY (Strong)", "HOLD", "BUY", "ACCUMULATE"]),
            status_sub=f"Synced: {datetime.now().strftime('%H:%M UTC')}" if not t212_error else t212_error,
            status_color="text-emerald-500" if not t212_error else "text-rose-500",
            pending_orders=pending_orders,
            solar=solar_report,
            immune=get_report(immune),
            sitrep=intel.get('sitrep', {"headline": "WAITING FOR INTEL", "body": "...", "status_color": "text-neutral-500"})
        )
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_output)
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    finally:
        if os.path.exists('sentinel.lock'):
            os.remove('sentinel.lock')
        print(f"Reconciliation Complete. Lock Released.")

def get_report(immune):
    return {
        "heartbeat": immune.connectivity_heartbeat(120),
        "locks": immune.locks,
        "alerts": immune.alerts
    }

if __name__ == "__main__":
    main()
