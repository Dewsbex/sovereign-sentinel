import sys
import os
import time
import time as sleep_time
from datetime import datetime, time as dtime, timedelta
from trading212_client import Trading212Client
from strategy_engine import SniperStrategy
from telegram_bot import SovereignAlerts
from audit_log import AuditLogger
from session_manager import SessionManager
import json

# --- HARD TIME LOCK ---
# US Market Hours (UTC): 14:25 to 21:05
START = dtime(14, 25)
END = dtime(21, 5)

def send_eod_report(alerts: SovereignAlerts, logger: AuditLogger):
    """Sends the End-of-Day summary report with P&L."""
    try:
        logger.log("EOD_REPORT_START", "System", "Generating End-of-Day Report")
        
        # Calculate Session P&L
        # Try to read baseline from ORB Shield
        initial_equity = 0.0
        current_equity = 0.0
        pnl_text = "N/A"
        
        try:
            client = Trading212Client()
            acct = client.get_account_info()
            current_equity = float(acct.get('totalValue', 0.0))
            
            if os.path.exists('data/shield_baseline.txt'):
                with open('data/shield_baseline.txt', 'r') as f:
                    lines = f.readlines()
                    initial_equity = float(lines[0].strip())
                    
                pnl = current_equity - initial_equity
                icon = "🟢" if pnl >= 0 else "🔴"
                pnl_text = f"{icon} £{pnl:,.2f}"
            else:
                pnl_text = "Baseline not recorded (Shield inactive?)"
        except Exception as e:
            pnl_text = f"Error calculating P&L: {e}"

        msg = (f"MARKET CLOSE (21:05 UTC)\n"
               f"**Session P&L**: {pnl_text}\n"
               f"Final Equity: £{current_equity:,.2f}\n\n"
               f"Session Status: COMPLETE\n"
               f"Sentinel entering sleep mode.")
        
        alerts.send_health_alert("main_bot.py", "✅ SESSION COMPLETE", msg)
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
        # v2.3 SESSION MANAGER (Emergency Fix)
        session_manager = SessionManager()
        logger.log("INIT_SUCCESS", "System", "All services loaded (Session Isolation Active)", "SUCCESS")
    except Exception as e:
        logger.log("INIT_FAILURE", "System", str(e), "CRITICAL")
        print(f"CRITICAL STARTUP ERROR: {e}")
        sys.exit(1)

    # State Tracking
    last_pulse_time = 0
    last_keepalive_time = 0
    open_brief_failures = 0  # v3.1: Track failures to prevent infinite retry

    # SAFETY: Check for Emergency Lock (Circuit Breaker)
    if os.path.exists('data/emergency.lock'):
        logger.log("EMERGENCY_LOCK", "System", "Circuit Breaker Triggered - Bot Disabled", "CRITICAL")
        print("EMERGENCY LOCK DETECTED. Bot disabled by Circuit Breaker.")
        while True:
            time.sleep(3600)


    while True:
        try:
            now_dt = datetime.utcnow()
            now_time = now_dt.time()
            now_ts = time.time()
            
            # 0. WEEKEND CHECK
            if now_dt.weekday() >= 5:
                # logger.log("WEEKEND_EXIT", "System", "Detected weekend, exiting.", "INFO")
                # print(f"⛔ MARKET CLOSED (Weekend). Sentinel Exiting.")
                # sys.exit(0)
                # v2.3 Fix: Sleep to prevent restart loop
                sleep_time.sleep(3600)
                continue

            # 0b. VACATION MODE CHECK (v3.0)
            is_vacation = os.path.exists("vacation.lock")
            if is_vacation:
                if now_ts - last_keepalive_time > 300:
                    print(f"VACATION MODE ACTIVE: Entries Paused. Risk Management Running.")
                    logger.log("VACATION_PULSE", "System", "Entries Paused", "INFO")
                    # Update heartbeat so we don't spam logs
                    last_keepalive_time = now_ts

            # 1. TIME WINDOW MANAGEMENT
            if now_time < START:
                # BEFORE 14:25 UTC - Standby Mode
                if now_ts - last_keepalive_time > 300: # Log every 5 mins
                     print(f"STANDBY: Market opens at {START} UTC. Current: {now_time.strftime('%H:%M:%S')}")
                     logger.log("STANDBY", "System", f"Waiting for {START}", "HEARTBEAT")
                     last_keepalive_time = now_ts
                sleep_time.sleep(60)
                continue
                
            if now_time > END:
                # AFTER 21:05 UTC - End of Day
                eod_lock = 'data/eod_report.lock'
                today_str = datetime.utcnow().strftime('%Y-%m-%d')
                
                # Check if we already sent the report today
                report_sent = False
                if os.path.exists(eod_lock):
                     with open(eod_lock, 'r') as f:
                         if f.read().strip() == today_str:
                             report_sent = True
                
                if not report_sent:
                    logger.log("SESSION_END", "System", "Past 21:05 UTC cutoff")
                    send_eod_report(alerts, logger)
                    # Mark as sent
                    with open(eod_lock, 'w') as f:
                        f.write(today_str)
                    print(f"🏁 SESSION ENDED. Report Sent. Enter Deep Sleep.")
                else:
                    # Report already sent, just log heartbeat occasionally
                    if now_ts - last_keepalive_time > 3600:
                        print(f"💤 NIGHT MODE: Waiting for {START} UTC. (Report already sent)")
                        last_keepalive_time = now_ts

                sleep_time.sleep(60)
                continue

            # 2. FORCE SESSION CLOSE (21:00 UTC - The Curfew)
            # (Run regardless of vacation to clear session trades)
            if now_time >= dtime(21, 0):
                print("21:00 UTC CURFEW: Closing SESSION positions.")
                try:
                    positions = client.get_positions()
                    if positions:
                        for pos in positions:
                            ticker = pos.get('ticker')
                            qty = pos.get('quantity')
                            
                            # v2.3 WHITELIST CHECK
                            if session_manager.is_whitelisted(ticker):
                                print(f"   Closing {ticker} ({qty}) for curfew.")
                                logger.log("CURFEW_CLOSE", ticker, f"Closing {qty} units", "WARNING")
                                client.execute_order(ticker, qty, "SELL")
                                # 🧾 RECORD SELL IN LEDGER
                                session_manager.record_sale(ticker, qty, 0.0) # Price fallback to 0 for curfew
                            else:
                                print(f"   PROTECTED: {ticker} ignored (Long-term Hold)")
                    else:
                        pass # No positions
                except Exception as e:
                    logger.log("CURFEW_ERROR", "System", str(e), "ERROR")
                
                sleep_time.sleep(60) # Wait out
                continue

            # 2a. 5-MINUTE ALIVE LOG
            if now_ts - last_keepalive_time > 300:
                status_msg = "Loop functioning normally"
                if is_vacation:
                    status_msg += " (VACATION MODE)"
                logger.log("ALIVE", "System", status_msg, "HEARTBEAT")
                last_keepalive_time = now_ts

            # 3. THE HUNT (Check Targets)
            # SKIPPED IF VACATION MODE ACTIVE
            if now_time >= dtime(14, 30) and not is_vacation:
                triggers = strategy.scan_market() 
                if triggers:
                    # IRON SEED CHECK
                    if not auditor.enforce_iron_seed():
                        logger.log("IRON_SEED_BLOCK", "System", "Lab Cap Met", "WARNING")
                        triggers = [] 
                    
                    # 🛡️ STRATEGIC HOLDINGS BLACKLIST (v2.4 - Portfolio Isolation)
                    strategic_blacklist = set()
                    if os.path.exists('data/strategic_holdings.json'):
                        try:
                            with open('data/strategic_holdings.json', 'r') as f:
                                blacklist_data = json.load(f)
                                strategic_blacklist = set(blacklist_data.get('tickers', []))
                                if strategic_blacklist:
                                    logger.log("STRATEGIC_GUARD_LOADED", "System", f"{len(strategic_blacklist)} protected tickers", "INFO")
                        except Exception as e:
                            logger.log("STRATEGIC_GUARD_ERROR", "System", str(e), "WARNING")
                        
                    for trade in triggers:
                        try:
                            ticker = trade['ticker']
                            
                            # 🛡️ STRATEGIC HOLDINGS GUARD (v2.4)
                            # Prevents Job C from buying tickers managed by Job A
                            if ticker in strategic_blacklist:
                                logger.log("STRATEGIC_BLOCK", ticker, "Protected by Job A blacklist", "WARNING")
                                alerts.send_message(f"⚠️ **CONFLICT DETECTED**\n{ticker} is a strategic holding.\nBlocking Job C entry to protect Job A portfolio.")
                                continue
                            
                            # VALIDATE TICKER
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
    
                            # APROMS IRONCLAD GAUNTLET (SPEC v2.1)
                            # 1. Volume Filter
                            import yfinance as yf
                            t_ticker = yf.Ticker(ticker)
                            t_info = t_ticker.info
                            
                            avg_vol = t_info.get('averageVolume', 0)
                            if not auditor.check_volume_filter(ticker, avg_vol):
                                logger.log("VOLUME_FILTER", ticker, f"Vol: {avg_vol}", "INFO")
                                continue 
                            
                            # 2. Spread Guard (Tight 0.05%)
                            bid = t_info.get('bid', 0)
                            ask = t_info.get('ask', 0)
                            if not (bid > 0 and ask > 0):
                                logger.log("DATA_WARNING", ticker, "No Bid/Ask data", "WARNING")
                                continue

                            if not auditor.check_spread_guard(ticker, bid, ask):
                                logger.log("SPREAD_GUARD", ticker, f"{bid}/{ask}", "INFO")
                                continue

                            # 3. VWAP Gate
                            if not auditor.check_vwap_gate(ticker, trade['price']):
                                logger.log("VWAP_GATE", ticker, "Price < VWAP, skipping Long", "INFO")
                                continue

                            # 4. Volatility Guard (ATR)
                            if not auditor.check_volatility_guard(ticker):
                                logger.log("VOL_GUARD", ticker, "Excessive ATR, skipping", "INFO")
                                continue

                            # 5. Dynamic Risk Calculator (APROMS SPEC)
                            acct = client.get_account_info()
                            total_wealth = float(acct.get('totalValue', 0.0))
                            realized_pnl = auditor.load_balance_state().get("realized_profit", 0.0)

                            # 4.5 BI-DIRECTIONAL RISK & GLOBAL CAP (SPEC vFinal.15)
                            # GLOBAL RISK CAP Check
                            is_capped, cap_reason = auditor.check_global_risk_cap(total_wealth)
                            if is_capped:
                                logger.log("GLOBAL_CAP", ticker, cap_reason, "WARNING")
                                continue

                            # Calculate floating P&L for Unrealized Mirror
                            floating_pnl = 0.0
                            current_positions = client.get_positions() # Refresh for accurate mirror
                            if current_positions:
                                for p in current_positions:
                                    if session_manager.is_whitelisted(p['ticker']):
                                        floating_pnl += float(p.get('ppl', 0.0))

                            # THE TESLA RULE (Mandatory Quality Exclusion)
                            TESLA_RULE_LIST = ["TSLA", "AMC", "GME", "DJT"]
                            if ticker in TESLA_RULE_LIST:
                                logger.log("TESLA_RULE", ticker, "Mandatory Volatility Exclusion", "WARNING")
                                continue

                            risk_pct = auditor.calculate_active_risk(0.01, realized_pnl, floating_pnl) # Start 1%
                            max_pos_value = total_wealth * risk_pct
                            
                            # Adjust quantity to fit risk
                            qty = max_pos_value / trade['price']
                            if qty < 1: qty = 1 # Minimum 1 share for prototype
                            
                            # EXECUTE BUY
                            logger.log("BUY_SIGNAL", ticker, f"Risk: {risk_pct:.2%}, Qty: {qty:.2f}", "SUCCESS")
                            client.execute_order(ticker, qty, "BUY")
                            
                            # 🧾 PERSISTENT LEDGER RECORD
                            session_manager.add_ticker(ticker, qty, trade['price'])
                            
                            trade_copy = trade.copy()
                            trade_copy['quantity'] = qty
                            alerts.send_trade_alert(trade_copy, "ENTRY")
                            
                        except Exception as e:
                             logger.log("TRADE_ERROR", ticker if 'ticker' in locals() else "Unknown", str(e), "ERROR")

            # 4. MARKET OPEN ANALYSIS (JOB A/C Hybrid)
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
                    
                    open_brief_failures = 0  # Reset on success
                    logger.log("OPEN_BRIEF_COMPLETE", "System", "Targets generated", "SUCCESS")

            except Exception as e:
                open_brief_failures += 1
                logger.log("OPEN_BRIEF_ERROR", "System", str(e), "ERROR")
                # v3.1: After 3 failures, write lock to stop infinite retry loop
                if open_brief_failures >= 3:
                    try:
                        with open('data/open_brief.lock', 'w') as f:
                            f.write(datetime.utcnow().strftime('%Y-%m-%d'))
                        logger.log("OPEN_BRIEF_ABORTED", "System", 
                                   f"Gave up after {open_brief_failures} failures: {e}", "CRITICAL")
                        alerts.send_health_alert("main_bot.py", "CRITICAL: OPEN BRIEF FAILED",
                                                 f"Morning Brief failed {open_brief_failures}x. Error: {str(e)[:100]}")
                    except Exception:
                        pass  # Lock write failure shouldn't crash the bot

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
                        ticker = trade['ticker']
                        # v2.3 WHITELIST CHECK (Redundant safety, but good)
                        if session_manager.is_whitelisted(ticker):
                            logger.log("EXIT_SIGNAL", ticker, f"Price: ${trade['price']:.2f} ({trade['reason']})", "SUCCESS")
                            client.execute_order(ticker, trade['quantity'], "SELL")
                            # 🧾 RECORD SELL IN LEDGER
                            session_manager.record_sale(ticker, trade['quantity'], trade['price'])
                            alerts.send_trade_alert(trade, "EXIT")
                        else:
                             # Strategy engine might return exits based on targets.json
                             # If a long term hold ended up in targets.json manually, this protects it.
                             logger.log("EXIT_BLOCKED", ticker, "Ignored Risk Exit (Not in Whitelist)", "WARNING")

            except Exception as e:
                logger.log("RISK_CHECK_ERROR", "System", str(e), "ERROR")

            # 7. HOURLY PULSE
            if now_ts - last_pulse_time > 3600:
                 try:
                    target_list = "No Targets"
                    if os.path.exists('data/targets.json'):
                        with open('data/targets.json', 'r') as f:
                             t_data = json.load(f)
                             tickers = [t['ticker'] for t in t_data]
                             target_list = ", ".join(tickers)
                    
                    alerts.send_pulse(len(tickers), now_dt.strftime('%H:%M'))
                    logger.log("PULSE_SENT", "System", f"Targets: {len(tickers)}", "INFO")
                    last_pulse_time = now_ts 
                    
                 except Exception as e:
                     logger.log("PULSE_ERROR", "System", str(e), "ERROR")

            # Loop beat
            # print(f".", end="", flush=True)
            sleep_time.sleep(60)

        except KeyboardInterrupt:
            logger.log("SHUTDOWN", "System", "User Interrupt", "WARNING")
            sys.exit(0)
        except Exception as e:
            # GLOBAL ERROR CATCH
            timestamp = datetime.utcnow().isoformat()
            print(f"\n⚠️ GLOBAL LOOP ERROR: {e}")
            try:
                logger.log("GLOBAL_ERROR", "System", str(e), "CRITICAL")
            except:
                pass
            sleep_time.sleep(60) 

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    run_sniper()
