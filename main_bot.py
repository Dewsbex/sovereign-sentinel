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
                        # VALIDATE TICKER (v2.1) - Double check (Client processes it too, but safe here)
                        if not client.validate_ticker(trade['ticker']):
                             print(f"⛔ Skipped Invalid Ticker: {trade['ticker']}")
                             continue

                        # EXECUTE BUY
                        print(f"🚀 BUY SIGNAL: {trade['ticker']} @ ${trade['price']:.2f}")
                        client.execute_order(trade['ticker'], trade['quantity'], "BUY")
                        alerts.send_trade_alert(trade, "ENTRY")
            else:
                print(f"⏳ PRE-MARKET: {now_time.strftime('%H:%M:%S')} UTC. Waiting for 14:30 open...")
        except Exception as e:
            print(f"⚠️ Scan Error: {e}")

        # 2.5 MARKET OPEN ANALYSIS (Job A/C Hybrid - 14:30 UTC)
        # Provides the highly requested "15-minute analysis summary" at open.
        try:
            if now_time >= dtime(14, 30) and now_time < dtime(14, 35):
                open_brief_lock = 'data/open_brief.lock'
                today_str = datetime.utcnow().strftime('%Y-%m-%d')
                
                run_open_brief = True
                if os.path.exists(open_brief_lock):
                    with open(open_brief_lock, 'r') as f:
                        if f.read().strip() == today_str:
                            run_open_brief = False
                
                if run_open_brief:
                    print("🔔 MARKET OPEN: Generating 15-Min Analysis Summary & TACTICAL PLAN...")
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
        sleep_time.sleep(60) # Scan every minute

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    run_sniper()
