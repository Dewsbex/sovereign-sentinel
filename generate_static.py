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
    
    # State Containers
    total_wealth = 0.0
    cash_reserves = 0.0
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

        # Cash
        r_account = make_request_with_retry(f"{BASE_URL}equity/account/cash", headers=headers, auth=(config.T212_API_KEY, config.T212_API_SECRET))
        cash_data = r_account.json() if (r_account and r_account.status_code == 200) else {}
        cash_reserves = parse_float(cash_data.get('free', 0)) / 100.0
        total_wealth = parse_float(cash_data.get('total', 0)) / 100.0

        # Portfolio
        r_portfolio = make_request_with_retry(f"{BASE_URL}equity/portfolio", headers=headers, auth=(config.T212_API_KEY, config.T212_API_SECRET))
        portfolio_raw = r_portfolio.json() if (r_portfolio and r_portfolio.status_code == 200) else []

        # 2. PROCESS PORTFOLIO THROUGH ORACLE & IMMUNE SYSTEM
        for pos in portfolio_raw:
            raw_ticker = pos.get('ticker', '')
            if not raw_ticker: continue
            
            # Ticker Mapping & Meta
            mapped_ticker = config.get_mapped_ticker(raw_ticker)
            meta = instrument_map.get(raw_ticker, {})
            currency = meta.get('currency') or pos.get('currency', '')
            
            # Financials
            qty = parse_float(pos.get('quantity', 0))
            raw_cur_price = parse_float(pos.get('currentPrice', 0))
            raw_avg_price = parse_float(pos.get('averagePrice', 0))
            
            # Currency Normalization (GBX -> GBP)
            is_uk = (currency in ['GBX', 'GBp']) or raw_ticker.endswith('.L')
            cur_price = raw_cur_price / 100.0 if is_uk else raw_cur_price
            avg_price = raw_avg_price / 100.0 if is_uk else raw_avg_price
            
            market_val = qty * cur_price
            invested = qty * avg_price
            pnl_pct = ((market_val - invested) / invested) if invested > 0 else 0
            
            # Immune System Check (Simplified Simulation)
            immune.check_stock_split_guard(mapped_ticker, 0.05) # Fake deviation
            
            # Oracle Audit (Simulated mock data for gates)
            # In a real system, these would be fetched from a financial data provider
            mock_data = {
                'sector': 'Technology', # Placeholder
                'moat': 'Wide',         # Placeholder
                'ocf': 1000,            # Placeholder
                'capex': 200,           # Placeholder
                'mcap': 10000           # Placeholder
            }
            audit = oracle.run_full_audit(mock_data)
            
            # Combine into Moat Audit Report
            moat_audit_data.append({
                'ticker': mapped_ticker,
                'origin': 'US' if currency == 'USD' else 'UK',
                'is_us': currency == 'USD',
                'net_yield': f"{audit['net_yield']*100:.2f}%",
                'pnl_pct': f"{pnl_pct*100:+.1f}%",
                'verdict': audit['verdict'],
                'action': "HOLD" if audit['verdict'] == "PASS" else "TRIM",
                'logic': "Meets v29.0 Master Spec" if audit['verdict'] == "PASS" else "Fails Risk-Free Hurdle"
            })

            # Heatmap Data
            heatmap_data.append({
                'x': mapped_ticker,
                'y': market_val,
                'fillColor': '#28a745' if pnl_pct >= 0 else '#dc3545',
                'custom_main': f"£{market_val:,.2f}",
                'custom_sub': f"{pnl_pct*100:+.1f}%"
            })

    except Exception as e:
        print(f"PORTFOLIO ERROR: {e}")
        t212_error = str(e)

    # 3. SECTOR GUARDIAN & INCOME CALENDAR (SPEC 6.3 - 6.4)
    sector_weights = {}
    for item in moat_audit_data:
        sector = "Technology" # In real use, fetch from meta
        sector_weights[sector] = sector_weights.get(sector, 0) + parse_float(item.get('weight', 0))
    
    sector_alerts = []
    for sector, weight in sector_weights.items():
        if weight > 0.35:
            sector_alerts.append(f"⚠️ SECTOR OVERWEIGHT: {sector} at {weight*100:.1f}%. Limit is 35%.")

    # 30-Day Dividend Forecast (Mock for Spec 6.4)
    income_calendar = [
        {"ticker": "VOD.L", "date": "2026-02-15", "amount": "£125.40"},
        {"ticker": "AAPL", "date": "2026-02-28", "amount": "£42.10"}
    ]

    # 4. GHOST PROTOCOL & DUAL PIPELINE
    # (Simulated merging of offline assets or intelligence)
    try:
        import fetch_intelligence
        intel = fetch_intelligence.run_intel()
        ghosts = intel.get('ghost_holdings', [])
        for g in ghosts:
            g_val = float(g.get('value', 0.0))
            total_wealth += g_val
            heatmap_data.append({
                'x': g.get('name', 'GHOST'),
                'y': g_val,
                'fillColor': '#6c757d',
                'custom_main': f"£{g_val:,.2f}",
                'custom_sub': "OFFLINE"
            })
    except Exception:
        intel = {"watchlist": [], "sitrep": {}}

    # 4. SOLAR CYCLE - TAX FORK & PHASES
    tax_report = solar.phase_4b_tax_logic_fork({})
    solar_report = {
        "phase": solar.phase,
        "tax": tax_report,
        "pre_market": solar.phase_1_pre_market()
    }

    # 5. GENERATE FINAL DASHBOARD
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())
    
    html_output = template.render(
        # ContextRoom
        env=config.ENVIRONMENT,
        risk_free=f"{config.RISK_FREE_RATE*100}%",
        drip=config.DRIP_STATUS,
        # Metrics
        total_value=f"£{total_wealth:,.2f}",
        cash_reserves=f"£{cash_reserves:,.2f}",
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
        # Solar Cycle
        solar=solar_report,
        immune=get_report(immune),
        sitrep=intel.get('sitrep', {"headline": "WAITING FOR INTEL", "body": "...", "status_color": "text-neutral-500"})
    )
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print("Build Complete (v29.0 MASTER).")

def get_report(immune):
    return {
        "heartbeat": immune.connectivity_heartbeat(120),
        "locks": immune.locks,
        "alerts": immune.alerts
    }

if __name__ == "__main__":
    main()
