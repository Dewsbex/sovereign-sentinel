import sys
import os
import time as sleep_time
from datetime import datetime, time as dtime
from trading212_client import Trading212Client
from strategy_engine import SniperStrategy
from telegram_bot import SovereignAlerts

# --- HARD TIME LOCK ---
# US Market Hours (UTC): 14:25 to 21:05
START = dtime(14, 25)
END = dtime(21, 5)

def run_sniper():
    """
    Sovereign Sniper Engine (Job C)
    Autonomous Execution and Risk Management Lifecycle.
    """
    # 0. INSTANT TIME CHECK (Die if outside 14:25-21:05 UTC)
    now_dt = datetime.utcnow()
    now_time = now_dt.time()
    
    if not (START <= now_time <= END) or now_dt.weekday() >= 5:
        print(f"⛔ MARKET CLOSED ({now_time.strftime('%H:%M:%S')} UTC). Sentinel Sleeping.")
        sys.exit(0)

    # Initialize Services
    client = Trading212Client()
    from auditor import TradingAuditor # Lazy import
    auditor = TradingAuditor()
    strategy = SniperStrategy(client)
    alerts = SovereignAlerts()
    
    # ... (startup msgs)

    while True:
        # 1. FORCE SESSION CLOSE (21:00 UTC - The Curfew)
        now_dt = datetime.utcnow()
        now_time = now_dt.time()
        
        if now_time >= dtime(21, 0):
            print("🌙 21:00 UTC CURFEW: Closing all intraday positions.")
            try:
                positions = client.get_positions()
                if positions:
                    for pos in positions:
                        print(f"   Closing {pos['ticker']} ({pos['quantity']}) for curfew.")
                        client.execute_order(pos['ticker'], pos['quantity'], "SELL")
                else:
                    print("   No open positions to close.")
            except Exception as e:
                print(f"⚠️ Curfew Error: {e}")
            
            # Sleep until midnight or exit? Script restarts daily via cron or effective loop constraints.
            # Just sleep for a while to avoid spamming API until 21:05 exit.
            sleep_time.sleep(300) 
            continue

        # 2. THE HUNT (Check Targets)
        try:
            if now_time >= dtime(14, 30):
                triggers = strategy.scan_market() 
                if triggers:
                    # IRON SEED CHECK (v2.1)
                    if not auditor.enforce_iron_seed():
                        print("🛑 IRON SEED BLOCK: Lab Cap Met. Skipping Trades.")
                        triggers = [] # Wipe triggers
                        
                    for trade in triggers:
                        ticker = trade['ticker']
                        
                        # VALIDATE TICKER (v2.1) - Double check (Client processes it too, but safe here)
                        if not client.validate_ticker(ticker):
                             print(f"⛔ Skipped Invalid Ticker: {ticker}")
                             continue

                        # DUPLICATE GUARD (Restart Safety)
                        # Prevents re-buying if we restart the bot mid-scan
                        # We check if we already hold this ticker
                        current_positions = client.get_positions()
                        is_held = False
                        if current_positions and isinstance(current_positions, list):
                            for p in current_positions:
                                if p.get('ticker') == ticker:
                                    is_held = True
                                    break
                        
                        if is_held:
                            print(f"⚠️ Skipping {ticker}: Position already held (Duplicate Guard).")
                            continue

                        # AUDITOR GAUNTLET (Safety Protocols)
                        try:
                            # We fetch detailed info here for the specific candidate
                            # This adds latency but ensures safety (The "Auditor")
                            import yfinance as yf
                            t_info = yf.Ticker(ticker).info
                            
                            # A. Volume Filter
                            avg_vol = t_info.get('averageVolume', 0)
                            if not auditor.check_volume_filter(ticker, avg_vol):
                                continue # Logged by auditor method

                            # B. Spread Guard
                            bid = t_info.get('bid', 0)
                            ask = t_info.get('ask', 0)
                            
                            # Only check if data available
                            if bid > 0 and ask > 0:
                                if not auditor.check_spread_guard(ticker, bid, ask):
                                    continue # Logged by auditor method
                            else:
                                print(f"⚠️ Spread Guard: No Bid/Ask for {ticker}. Proceeding (Data Unavailable).")

                        except Exception as e:
                            print(f"⚠️ Auditor Check Error ({ticker}): {e}")
                            # On error, we allow trade but warn. (Fail Open for data errors, Fail Closed for logic)
                        
                        # EXECUTE BUY
                        print(f"🚀 BUY SIGNAL: {ticker} @ ${trade['price']:.2f}")
                        client.execute_order(ticker, trade['quantity'], "BUY")
                        alerts.send_trade_alert(trade, "ENTRY")
            else:
                print(f"⏳ PRE-MARKET: {now_time.strftime('%H:%M:%S')} UTC. Waiting for 14:30 open...")
        except Exception as e:
            print(f"⚠️ Scan Error: {e}")

        # 2.5 MARKET OPEN ANALYSIS (Job A/C Hybrid - 14:30 UTC)
        # Provides the highly requested "15-minute analysis summary" at open.
        # 2.5 MARKET OPEN ANALYSIS (Job A/C Hybrid - 14:30 UTC)
        # Provides the highly requested "15-minute analysis summary" at open.
        # v2.2 LATE-START BACKFILL: If we miss the 14:30 window (e.g. restart at 19:00),
        # we MUST still run this to generate targets for the rest of the session.
        try:
            open_brief_lock = 'data/open_brief.lock'
            today_str = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Check if we have already run for today
            has_run_today = False
            if os.path.exists(open_brief_lock):
                 with open(open_brief_lock, 'r') as f:
                     if f.read().strip() == today_str:
                         has_run_today = True
            
            # Logic: Run if time > 14:30 AND (Time < 21:00) AND Not Run Today
            # This covers both the scheduled 14:30 slot AND any late start backfill
            if now_time >= dtime(14, 30) and now_time < dtime(21, 0) and not has_run_today:
                
                is_backfill = now_time >= dtime(14, 35)
                print(f"🔔 OPEN BRIEF PROCOTOL: Initiating (Backfill Mode: {is_backfill})")
                
                from strategic_moat import MorningBrief
                
                # Run analysis AND generate targets (Morning Brief)
                brief = MorningBrief()
                brief.generate_brief()
                
                # Lock it
                with open(open_brief_lock, 'w') as f:
                    f.write(today_str)
                print("✅ Open Brief Sent & Targets Generated.")

        except Exception as e:
            print(f"⚠️ Open Brief Error: {e}")

        # 2a. APROMS REBALANCING (Job B - 15:00 UTC)
        # Executes once per day to align with Macro Clock
        try:
            # Run only between 15:00 and 15:05
            if now_time >= dtime(15, 0) and now_time < dtime(15, 5):
                # Check safeguards - Only rebalance if we haven't already
                rebalance_lock = 'data/rebalance.lock'
                today_str = datetime.utcnow().strftime('%Y-%m-%d')
                
                run_rebalance = True
                if os.path.exists(rebalance_lock):
                    with open(rebalance_lock, 'r') as f:
                        if f.read().strip() == today_str:
                            run_rebalance = False
                
                if run_rebalance:
                    print("⚖️ APROMS: Initiating Sector Rebalance Sequence...")
                    from strategic_moat import SectorMapper
                    from macro_clock import MacroClock
                    
                    mapper = SectorMapper()
                    clock = MacroClock()
                    phase_data = clock.detect_market_phase()
                    report = mapper.generate_delta_report()
                    
                    print(f"   Phase: {phase_data['phase']}")
                    print(f"   Delta Report: {report}")
                    
                    # Log completion to lock file
                    with open(rebalance_lock, 'w') as f:
                        f.write(today_str)
                    
                    alerts.send_message(f"⚖️ **APROMS REBALANCING**\nPhase: {phase_data['phase']}\n\n{report}")
                    
        except Exception as e:
             print(f"⚠️ APROMS Error: {e}")

        # 3. THE SHIELD (Check Exits)
        # Checks every open position for Stop Loss / Take Profit
        try:
            exits = strategy.check_risk_rules()
            if exits:
                for trade in exits:
                    # EXECUTE SELL
                    print(f"🛑 EXIT SIGNAL: {trade['ticker']} @ ${trade['price']:.2f}")
                    client.execute_order(trade['ticker'], trade['quantity'], "SELL")
                    alerts.send_trade_alert(trade, "EXIT")
        except Exception as e:
            print(f"⚠️ Risk Error: {e}")

        print(f"... Heartbeat {datetime.now().strftime('%H:%M:%S')} ...")
        
        # 4. HOURLY PULSE (Proof of Life)
        # Sends a Telegram message at the top of every hour (XX:00)
        current_hour = now_dt.hour
        # specific check to avoid spamming (using minute 0 and a lock variable notion)
        # We can use a simple file lock or just rely on the sleep(60)
        if now_dt.minute == 0:
             pulse_lock = f"data/pulse_{now_dt.strftime('%Y%m%d_%H')}.lock"
             if not os.path.exists(pulse_lock):
                 try:
                    # Get monitored targets
                    target_list = "No Targets Loaded"
                    if os.path.exists('data/targets.json'):
                        with open('data/targets.json', 'r') as f:
                             t_data = json.load(f)
                             tickers = [t['ticker'] for t in t_data]
                             target_list = ", ".join(tickers)
                    
                    msg = (f"💓 **SENTINEL PULSE**\n"
                           f"Time: {now_dt.strftime('%H:%M')} UTC\n"
                           f"Status: ACTIVE (Scanning)\n"
                           f"Targets: {target_list}")
                    
                    alerts.send_message(msg)
                    print(f"💓 Sent Hourly Pulse: {target_list}")
                    
                    with open(pulse_lock, 'w') as f:
                        f.write(str(now_dt))
                 except Exception as e:
                     print(f"⚠️ Pulse Error: {e}")

        sleep_time.sleep(60) # Scan every minute

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    run_sniper()
