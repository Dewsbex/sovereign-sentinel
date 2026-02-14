import sys
import os
import time
import time as sleep_time
from datetime import datetime, time as dtime, timedelta
from trading212_client import Trading212Client
from strategy_engine import SniperStrategy
from telegram_bot import SovereignAlerts
from audit_log import AuditLogger

# --- HARD TIME LOCK ---
# US Market Hours (UTC): 14:25 to 21:05
START = dtime(14, 25)
END = dtime(21, 5)

def send_eod_report(alerts: SovereignAlerts, logger: AuditLogger):
    """Sends the End-of-Day summary report."""
    try:
        logger.log("EOD_REPORT_START", "System", "Generating End-of-Day Report")
        
        # Gather stats (basic implementation - could read from today's audit log later)
        # For now, just a confirmation of session end.
        
        msg = (f"🏁 **MARKET CLOSE (21:05 UTC)**\n"
               f"Session Status: COMPLETE\n"
               f"Audit Log: `data/audit_log.csv`\n"
               f"Sentinel entering sleep mode.")
        
        alerts.send_message(msg)
        logger.log("EOD_REPORT_SENT", "System", "Report dispatched to Telegram", "SUCCESS")
        
    except Exception as e:
        logger.log("EOD_REPORT_ERROR", "System", str(e), "ERROR")

def run_sniper():
    """
    Sovereign Sniper Engine (Job C)
    Autonomous Execution and Risk Management Lifecycle.
    """
    # Initialize Logger
    logger = AuditLogger("SS007-MainBot")
    logger.log("STARTUP", "System", "Initializing Sniper Engine...", "INFO")

    # Initialize Services
    try:
        client = Trading212Client()
        from auditor import TradingAuditor # Lazy import
        auditor = TradingAuditor()
        strategy = SniperStrategy(client)
        alerts = SovereignAlerts()
        logger.log("INIT_SUCCESS", "System", "All services loaded", "SUCCESS")
    except Exception as e:
        logger.log("INIT_FAILURE", "System", str(e), "CRITICAL")
        print(f"🔥 CRITICAL STARTUP ERROR: {e}")
        sys.exit(1)

    # State Tracking
    last_pulse_time = 0
    last_keepalive_time = 0

    while True:
        try:
            now_dt = datetime.utcnow()
            now_time = now_dt.time()
            now_ts = time.time()
            
            # 0. WEEKEND CHECK
            if now_dt.weekday() >= 5:
                logger.log("WEEKEND_EXIT", "System", "Detected weekend, exiting.", "INFO")
                print(f"⛔ MARKET CLOSED (Weekend). Sentinel Exiting.")
                sys.exit(0)

            # 1. TIME WINDOW MANAGEMENT
            if now_time < START:
                # BEFORE 14:25 UTC - Standby Mode
                # Checks every minute but does not exit.
                if now_ts - last_keepalive_time > 300: # Log every 5 mins
                     print(f"💤 STANDBY: Market opens at {START} UTC. Current: {now_time.strftime('%H:%M:%S')}")
                     logger.log("STANDBY", "System", f"Waiting for {START}", "HEARTBEAT")
                     last_keepalive_time = now_ts
                sleep_time.sleep(60)
                continue
                
            if now_time > END:
                # AFTER 21:05 UTC - End of Day
                logger.log("SESSION_END", "System", "Past 21:05 UTC cutoff")
                send_eod_report(alerts, logger)
                print(f"🏁 SESSION ENDED. Exiting.")
                sys.exit(0)

            # 2. FORCE SESSION CLOSE (21:00 UTC - The Curfew)
            if now_time >= dtime(21, 0):
                print("🌙 21:00 UTC CURFEW: Closing all intraday positions.")
                try:
                    positions = client.get_positions()
                    if positions:
                        for pos in positions:
                            ticker = pos.get('ticker')
                            qty = pos.get('quantity')
                            print(f"   Closing {ticker} ({qty}) for curfew.")
                            logger.log("CURFEW_CLOSE", ticker, f"Closing {qty} units", "WARNING")
                            client.execute_order(ticker, qty, "SELL")
                    else:
                        pass # No positions
                except Exception as e:
                    logger.log("CURFEW_ERROR", "System", str(e), "ERROR")
                
                sleep_time.sleep(60) # Wait out the curfew window until 21:05 exit
                continue

            # 2a. 5-MINUTE ALIVE LOG (User requested "write every action and time")
            if now_ts - last_keepalive_time > 300:
                logger.log("ALIVE", "System", "Loop functioning normally", "HEARTBEAT")
                last_keepalive_time = now_ts

            # 3. THE HUNT (Check Targets)
            if now_time >= dtime(14, 30):
                triggers = strategy.scan_market() 
                if triggers:
                    # IRON SEED CHECK (v2.1)
                    if not auditor.enforce_iron_seed():
                        logger.log("IRON_SEED_BLOCK", "System", "Lab Cap Met", "WARNING")
                        triggers = [] 
                        
                    for trade in triggers:
                        try:
                            ticker = trade['ticker']
                            
                            # VALIDATE TICKER (v2.1)
                            if not client.validate_ticker(ticker):
                                 logger.log("INVALID_TICKER", ticker, "Skipped invalid ticker", "WARNING")
                                 continue
    
                            # DUPLICATE GUARD
                            current_positions = client.get_positions()
                            is_held = False
                            if current_positions and isinstance(current_positions, list):
                                for p in current_positions:
                                    if p.get('ticker') == ticker:
                                        is_held = True
                                        break
                            
                            if is_held:
                                logger.log("DUPLICATE_GUARD", ticker, "Position already held", "INFO")
                                continue
    
                            # AUDITOR GAUNTLET
                            import yfinance as yf
                            t_info = yf.Ticker(ticker).info
                            
                            avg_vol = t_info.get('averageVolume', 0)
                            if not auditor.check_volume_filter(ticker, avg_vol):
                                logger.log("VOLUME_FILTER", ticker, f"Vol: {avg_vol}", "INFO")
                                continue 
    
                            bid = t_info.get('bid', 0)
                            ask = t_info.get('ask', 0)
                            
                            if bid > 0 and ask > 0:
                                if not auditor.check_spread_guard(ticker, bid, ask):
                                    logger.log("SPREAD_GUARD", ticker, f"{bid}/{ask}", "INFO")
                                    continue
                            else:
                                logger.log("DATA_WARNING", ticker, "No Bid/Ask data", "WARNING")
                                
                            # EXECUTE BUY
                            logger.log("BUY_SIGNAL", ticker, f"Price: ${trade['price']:.2f}", "SUCCESS")
                            client.execute_order(ticker, trade['quantity'], "BUY")
                            alerts.send_trade_alert(trade, "ENTRY")
                            
                        except Exception as e:
                             logger.log("TRADE_ERROR", ticker if 'ticker' in locals() else "Unknown", str(e), "ERROR")

            # 4. MARKET OPEN ANALYSIS (JOB A/C Hybrid)
            # Run exactly once per day, between 14:30 and 21:00
            try:
                open_brief_lock = 'data/open_brief.lock'
                today_str = datetime.utcnow().strftime('%Y-%m-%d')
                
                has_run_today = False
                if os.path.exists(open_brief_lock):
                     with open(open_brief_lock, 'r') as f:
                         if f.read().strip() == today_str:
                             has_run_today = True
                
                if now_time >= dtime(14, 30) and not has_run_today:
                    
                    is_backfill = now_time >= dtime(14, 35)
                    logger.log("OPEN_BRIEF_START", "System", f"Backfill: {is_backfill}")
                    
                    from strategic_moat import MorningBrief
                    brief = MorningBrief()
                    brief.generate_brief()
                    
                    with open(open_brief_lock, 'w') as f:
                        f.write(today_str)
                    
                    logger.log("OPEN_BRIEF_COMPLETE", "System", "Targets generated", "SUCCESS")

            except Exception as e:
                logger.log("OPEN_BRIEF_ERROR", "System", str(e), "ERROR")

            # 5. APROMS REBALANCING (Job B - 15:00 UTC)
            try:
                if now_time >= dtime(15, 0) and now_time < dtime(15, 5):
                    rebalance_lock = 'data/rebalance.lock'
                    today_str = datetime.utcnow().strftime('%Y-%m-%d')
                    
                    if not os.path.exists(rebalance_lock) or open(rebalance_lock).read().strip() != today_str:
                        logger.log("APROMS_START", "System", "Rebalancing...")
                        from strategic_moat import SectorMapper
                        from macro_clock import MacroClock
                        
                        mapper = SectorMapper()
                        clock = MacroClock()
                        phase_data = clock.detect_market_phase()
                        report = mapper.generate_delta_report()
                        
                        with open(rebalance_lock, 'w') as f:
                            f.write(today_str)
                        
                        alerts.send_message(f"⚖️ **APROMS REBALANCING**\nPhase: {phase_data['phase']}\n\n{report}")
                        logger.log("APROMS_COMPLETE", "System", f"Phase: {phase_data['phase']}", "SUCCESS")
                        
            except Exception as e:
                 logger.log("APROMS_ERROR", "System", str(e), "ERROR")

            # 6. THE SHIELD (Check Exits)
            try:
                exits = strategy.check_risk_rules()
                if exits:
                    for trade in exits:
                        logger.log("EXIT_SIGNAL", trade['ticker'], f"Price: ${trade['price']:.2f}", "SUCCESS")
                        client.execute_order(trade['ticker'], trade['quantity'], "SELL")
                        alerts.send_trade_alert(trade, "EXIT")
            except Exception as e:
                logger.log("RISK_CHECK_ERROR", "System", str(e), "ERROR")

            # 7. HOURLY PULSE (Robust - Every 60 minutes)
            if now_ts - last_pulse_time > 3600:
                 try:
                    # Get monitored targets
                    target_list = "No Targets"
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
                    logger.log("PULSE_SENT", "System", f"Targets: {len(tickers)}", "INFO")
                    last_pulse_time = now_ts # Update timestamp
                    
                 except Exception as e:
                     logger.log("PULSE_ERROR", "System", str(e), "ERROR")

            # Loop beat
            print(f".", end="", flush=True)
            sleep_time.sleep(60)

        except KeyboardInterrupt:
            logger.log("SHUTDOWN", "System", "User Interrupt", "WARNING")
            sys.exit(0)
        except Exception as e:
            # GLOBAL ERROR CATCH - Prevents crash loop
            timestamp = datetime.utcnow().isoformat()
            print(f"\n⚠️ GLOBAL LOOP ERROR: {e}")
            try:
                # Try to log using our instance if valid, else print
                logger.log("GLOBAL_ERROR", "System", str(e), "CRITICAL")
            except:
                pass
            sleep_time.sleep(60) # Wait a bit before retrying

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    run_sniper()

