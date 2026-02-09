"""
ORB Shield - High-Frequency Circuit Breaker
============================================

Polls Trading 212 API every 5 seconds during active trading (14:30-21:00 UTC).
Records baseline equity at 14:29 UTC and triggers emergency shutdown if session loss exceeds £1,000.

Kill Protocol:
1. Send SIGTERM to main_bot.py
2. Wait 1 second
3. Directly call client.close_all_positions()
"""

import os
import sys
import time
import signal
from datetime import datetime, timezone
from typing import Optional
from trading212_client import Trading212Client


class ORBShield:
    """5-Second Polling Circuit Breaker"""
    
    def __init__(self, bot_pid: Optional[int] = None):
        self.client = Trading212Client()
        self.bot_pid = bot_pid
        
        # Circuit breaker threshold
        self.max_session_loss = 1000.0  # £1,000
        
        # Baseline tracking
        self.initial_equity: Optional[float] = None
        self.baseline_recorded = False
        
        # Polling interval
        self.poll_interval = 5  # seconds
        
    def get_current_equity(self) -> float:
        """
        Fetch current account equity from Trading 212.
        Uses /api/v0/equity/account/summary endpoint.
        """
        try:
            account = self.client.get_account_info()
            return float(account.get('totalValue', 0.0))
        except Exception as e:
            print(f"❌ Failed to fetch equity: {e}")
            return 0.0
    
    def record_baseline(self):
        """
        Record initial equity at 14:29 UTC (1 minute before ORB window).
        """
        current_time = datetime.now(timezone.utc)
        hour, minute = current_time.hour, current_time.minute
        
        if hour == 14 and minute == 29 and not self.baseline_recorded:
            self.initial_equity = self.get_current_equity()
            self.baseline_recorded = True
            print(f"📊 Baseline recorded at 14:29 UTC: £{self.initial_equity:,.2f}")
            
            # Write to file for persistence across restarts
            os.makedirs('data', exist_ok=True)
            with open('data/shield_baseline.txt', 'w') as f:
                f.write(f"{self.initial_equity}\n{current_time.isoformat()}")
    
    def load_baseline(self) -> bool:
        """
        Load baseline from file if shield was restarted mid-session.
        """
        try:
            if os.path.exists('data/shield_baseline.txt'):
                with open('data/shield_baseline.txt', 'r') as f:
                    lines = f.readlines()
                    self.initial_equity = float(lines[0].strip())
                    baseline_time = datetime.fromisoformat(lines[1].strip())
                    
                    # Only use if from today
                    if baseline_time.date() == datetime.now(timezone.utc).date():
                        self.baseline_recorded = True
                        print(f"📊 Loaded baseline from file: £{self.initial_equity:,.2f}")
                        return True
            return False
        except Exception as e:
            print(f"⚠️  Failed to load baseline: {e}")
            return False
    
    def check_session_loss(self) -> bool:
        """
        Calculate current session loss and trigger kill protocol if >£1,000.
        """
        if not self.baseline_recorded or self.initial_equity is None:
            return False
        
        current_equity = self.get_current_equity()
        if current_equity == 0: return False # Skip on transient errors
        
        session_pnl = current_equity - self.initial_equity
        
        print(f"⚡ Shield Check: Session P/L = £{session_pnl:+,.2f} | Equity: £{current_equity:,.2f}")
        
        if session_pnl <= -self.max_session_loss:
            session_loss = abs(session_pnl)
            print(f"🚨 CIRCUIT BREAKER TRIGGERED: Session loss £{session_loss:,.2f} >= £{self.max_session_loss}")
            self.execute_kill_protocol(session_loss, current_equity)
            return True
        
        return False
    
    def execute_kill_protocol(self, session_loss: float, current_equity: float):
        """
        Emergency shutdown sequence.
        """
        print(f"💥 Session Loss: £{session_loss:.2f} (exceeds £{self.max_session_loss} threshold)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🚨 EXECUTING KILL PROTOCOL")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # STEP 1: Write atomic kill flag (v1.9.4 - prevents main_bot race condition)
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/emergency.lock', 'w') as f:
                f.write(f"CIRCUIT_BREAKER_TRIGGERED\n")
                f.write(f"Timestamp: {datetime.now(timezone.utc).isoformat()}Z\n")
                f.write(f"Session Loss: £{session_loss:.2f}\n")
                f.write(f"Initial Equity: £{self.initial_equity:.2f}\n")
                f.write(f"Current Equity: £{current_equity:.2f}\n")
            print("   ✅ Atomic kill flag written: data/emergency.lock")
        except Exception as e:
            print(f"   ⚠️  Failed to write emergency.lock: {e}")
        
        # Step 1: Send SIGTERM to bot
        if self.bot_pid:
            try:
                os.kill(self.bot_pid, signal.SIGTERM)
                print(f"   ✅ Sent SIGTERM to bot (PID {self.bot_pid})")
            except Exception as e:
                print(f"   ⚠️  Failed to terminate bot: {e}")
        
        # Step 2: Wait 1 second
        time.sleep(1)
        
        # Step 3: Close all positions
        try:
            positions = self.client.get_positions()
            for pos in positions:
                ticker = pos['ticker']
                quantity = pos['quantity']
                
                # Market sell order
                self.client.place_market_order(
                    ticker=ticker,
                    quantity=quantity,
                    side='SELL'
                )
                print(f"   🔴 Closed position: {ticker} ({quantity} shares)")
            
            print("✅ All positions closed")
            
        except Exception as e:
            print(f"❌ Failed to close positions: {e}")
        
        # Send Telegram alert
        self.send_telegram_alert()
        
        # Exit shield
        sys.exit(0)
    
    def send_telegram_alert(self):
        """Send emergency alert via Telegram"""
        import requests
        
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not (token and chat_id):
            print("⚠️  Telegram credentials not configured")
            return
        
        message = (
            "🚨 ORB SHIELD: CIRCUIT BREAKER ACTIVATED\n\n"
            f"Session loss exceeded £{self.max_session_loss}\n"
            f"Initial equity: £{self.initial_equity:,.2f}\n"
            f"All positions closed.\n\n"
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}Z"
        )
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": message})
            print("✅ Telegram alert sent")
        except Exception as e:
            print(f"❌ Failed to send Telegram alert: {e}")
    
    def run(self):
        """
        Main shield loop.
        Runs from 14:25 UTC (pre-flight) until 21:00 UTC (market close).
        """
        print("🛡️  ORB Shield starting...")
        
        # Try to load existing baseline
        self.load_baseline()
        
        while True:
            current_time = datetime.now(timezone.utc)
            hour, minute = current_time.hour, current_time.minute
            
            # Active window: 14:25 - 21:00 UTC
            if hour == 14 and minute >= 25:
                # Record baseline at 14:29
                if minute == 29:
                    self.record_baseline()
                
                # Start monitoring at 14:30
                if minute >= 30 and self.baseline_recorded:
                    if self.check_session_loss():
                        break  # Circuit breaker triggered
            
            elif hour >= 15 and hour < 21:
                # Active trading hours
                if self.baseline_recorded:
                    if self.check_session_loss():
                        break
            
            elif hour >= 21:
                print("✅ Market closed, shield deactivating")
                break
            
            # Sleep for poll interval
            time.sleep(self.poll_interval)


def main():
    """CLI for running ORB Shield"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ORB Shield - Circuit Breaker')
    parser.add_argument('--bot-pid', type=int, help='PID of main_bot.py process')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no actual trades)')
    
    args = parser.parse_args()
    
    shield = ORBShield(bot_pid=args.bot_pid)
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE - No positions will be closed")
        # Override execute_kill_protocol for dry run
        shield.execute_kill_protocol = lambda: print("🛑 [DRY RUN] Kill protocol would be executed")
    
    try:
        shield.run()
    except KeyboardInterrupt:
        print("\n🛑 Shield stopped by user")


if __name__ == '__main__':
    main()
