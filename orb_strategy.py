
import json
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from trading212_client import Trading212Client
from telegram_bot import SovereignAlerts

def run_recovery():
    print("🚑 INITIATING ORB RECOVERY PROTOCOL...")
    
    # 1. Load Universe
    try:
        with open('data/master_universe.json', 'r') as f:
            data = json.load(f)
            tickers = [i['ticker'] for i in data.get('instruments', [])]
    except:
        tickers = ['NVDA', 'TSLA', 'AMD', 'SPY', 'QQQ', 'MSTR', 'COIN', 'PLTR']

    print(f"📊 Scanning {len(tickers)} tickers for 15-min ORB...")

    # 2. Fetch Today's 1m Data
    try:
        df = yf.download(tickers, period="1d", interval="1m", progress=False, group_by='ticker')
    except Exception as e:
        print(f"❌ Data fetch failed: {e}")
        return

    orb_targets = []
    
    # 3. Analyze Each Ticker
    print("DEBUG: Checking data samples...")
    
    for t in tickers:
        try:
            if len(tickers) > 1:
                if t not in df.columns.levels[0]: continue
                data = df[t].copy()
            else:
                data = df.copy()
            
            # Drop NaNs to ensure we have real data
            data.dropna(subset=['High', 'Low', 'Close'], inplace=True)
            
            if data.empty: 
                continue
            
            # Filter for TODAY's session (America/New_York)
            # data.index should be datetime with tz
            # We want the first 15 rows of the LATEST day's session
            
            # Simple heuristic: Take last 100 rows, group by date, take today's
            # But with 1m interval, period='1d' should only be today.
            # If it's NaN, maybe period='1d' failed to get today's data?
            
            # Check if we have data for today
            last_dt = data.index[-1]
            if last_dt.date() != datetime.utcnow().date():
                 # fallback for timezone diffs if running late/early?
                 pass

            orb_window = data.iloc[:15] 
            
            if len(orb_window) < 1: continue

            orb_high = orb_window['High'].max()
            orb_low = orb_window['Low'].min()
            orb_open = orb_window['Open'].iloc[0]
            orb_close = orb_window['Close'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            if pd.isna(orb_high) or pd.isna(orb_low):
                continue

            # --- VOLATILITY FILTER ---
            # Range must be significant enough to trade
            range_abs = orb_high - orb_low
            range_pct = (range_abs / orb_low) * 100
            
            # Filter 1: Minimum Volatility (0.8% range in first 15m)
            if range_pct < 0.8:
                continue

            # Filter 2: Directional Bias (Green 15m Candle)
            # We only want to buy strength
            if orb_close < orb_open:
                continue
                
            entry = {
                "ticker": t,
                "trigger_price": round(float(orb_high), 2),
                "stop_loss": round(float(orb_low), 2),
                "quantity": 3, 
                "orb_high": round(float(orb_high), 2),
                "orb_low": round(float(orb_low), 2),
                "range_pct": round(float(range_pct), 2),
                "current": round(float(current_price), 2),
                "added_by": "ORB Recovery"
            }
            
            orb_targets.append(entry)
            print(f"   {t}: QUALIFIED (Range: {range_pct:.2f}%) | £{entry['orb_high']} - £{entry['orb_low']}")
            
        except Exception as e:
            # print(f"Error processing {t}: {e}")
            continue

    # 4. Save Targets
    os.makedirs('data', exist_ok=True)
    with open('data/targets.json', 'w') as f:
        json.dump(orb_targets, f, indent=2)
        
    print(f"✅ Saved {len(orb_targets)} ORB targets.")
    
    # 5. Notify (Clean List Only)
    msg = f"🚑 **ORB QUALIFIED TARGETS ({len(orb_targets)})**\n"
    msg += "Job: `orb_strategy.py`\n"
    msg += "Criteria: Range > 0.8% & Green 15m Candle\n\n"
    
    # Sort by Volatility (Range %)
    orb_targets.sort(key=lambda x: x['range_pct'], reverse=True)
    
    count = 0
    for t in orb_targets:
        dist = (t['current'] - t['trigger_price']) / t['trigger_price'] * 100
        
        icon = "⚪"
        if t['current'] > t['trigger_price']: icon = "🚀"
        elif dist > -0.5: icon = "⚠️"
        
        msg += f"{icon} **{t['ticker']}** ({t['range_pct']}%) > {t['trigger_price']}\n"
        count += 1
        if count >= 30:
            msg += f"... and {len(orb_targets) - 30} more."
            break
            
    if not orb_targets:
        msg += "⚠️ No tickers qualified (Low volatility session?)"
    
    SovereignAlerts().send_message(msg)

if __name__ == "__main__":
    from audit_log import AuditLogger
    
    logger = AuditLogger("SS015-ORBStrategy")
    logger.log("JOB_START", "Strategy", "Analyzing 15m Open Range...")
    
    try:
        run_recovery()
        logger.log("JOB_COMPLETE", "Strategy", "Analysis Complete", "SUCCESS")
    except Exception as e:
        logger.log("JOB_ERROR", "Strategy", f"Analysis Failed: {e}", "ERROR")
        print(f"Critical Error: {e}")
