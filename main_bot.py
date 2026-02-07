"""
Job C Scalper - Sovereign Sentinel v1.9.1
==========================================

15-Minute ORB Strategy with Zombie Recovery Protocol

CRITICAL FEATURES:
- Zombie Recovery: Alpha Vantage retry loop (60s) with 15:15 UTC stale-data cutoff
- 15m ORB Window: 14:30-14:45 UTC
- Trigger: 5m candle CLOSE outside range
- Safety: Spread < 0.15%, Volume > 150%, Range < 2.5%
- Integration: trading212_client.py + data/instruments.json validation
"""

import os
import sys
import time
import json
import signal
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
from trading212_client import Trading212Client
from auditor import TradingAuditor


class ZombieRecovery:
    """Alpha Vantage failure resilience with stale-data cutoff"""
    
    STALE_CUTOFF_UTC = (15, 15)  # 15:15 UTC
    RETRY_INTERVAL = 60  # seconds
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        
    def fetch_intraday_data(self) -> Optional[yf.Ticker]:
        """
        Attempt to fetch intraday data via yfinance.
        Returns Ticker object if successful, None otherwise.
        """
        try:
            ticker_obj = yf.Ticker(self.ticker)
            # Validate data availability
            hist = ticker_obj.history(period='1d', interval='1m')
            if hist.empty:
                return None
            return ticker_obj
        except Exception as e:
            print(f"❌ Data fetch failed for {self.ticker}: {e}")
            return None
    
    def enter_retry_loop(self) -> Tuple[Optional[yf.Ticker], bool]:
        """
        ZOMBIE RECOVERY: Retry every 60s until success or stale cutoff.
        
        Returns:
            (ticker_obj, is_stale)
            - ticker_obj: yfinance Ticker if recovered, None if permanently failed
            - is_stale: True if recovery happened AFTER 15:15 UTC
        """
        print(f"\n🧟 ZOMBIE RECOVERY ACTIVATED for {self.ticker}")
        print("   Entering retry loop (60s interval)...\n")
        
        while True:
            current_time = datetime.now(timezone.utc)
            hour, minute = current_time.hour, current_time.minute
            
            # Attempt data fetch
            ticker_obj = self.fetch_intraday_data()
            
            if ticker_obj:
                # Success! Check if stale
                stale_cutoff_hour, stale_cutoff_min = self.STALE_CUTOFF_UTC
                is_stale = (hour > stale_cutoff_hour) or (hour == stale_cutoff_hour and minute >= stale_cutoff_min)
                
                if is_stale:
                    print(f"⚠️  STALE DATA DETECTED")
                    print(f"   Recovery time: {current_time.strftime('%H:%M:%S')} UTC")
                    print(f"   Cutoff: {stale_cutoff_hour:02d}:{stale_cutoff_min:02d} UTC")
                    print(f"   → Will NOT trade. Logging theoretical signal only.\n")
                else:
                    print(f"✅ ZOMBIE RECOVERY SUCCESSFUL")
                    print(f"   Recovery time: {current_time.strftime('%H:%M:%S')} UTC")
                    print(f"   → Within cutoff. Proceeding with retrospective ORB.\n")
                
                return ticker_obj, is_stale
            
            # Still failing - wait and retry
            print(f"⏳ Retry #{int(time.time()) % 1000} at {current_time.strftime('%H:%M:%S')} UTC - Next in 60s...")
            time.sleep(self.RETRY_INTERVAL)


class ORBEngine:
    """15-Minute Opening Range Breakout Calculator"""
    
    ORB_START_UTC = (14, 30)  # 14:30 UTC
    ORB_END_UTC = (14, 45)    # 14:45 UTC
    
    @staticmethod
    def calculate_orb_retrospective(ticker_obj: yf.Ticker) -> Dict:
        """
        Retrospectively calculate 14:30-14:45 UTC ORB metrics.
        Used after Zombie Recovery to reconstruct missed data.
        
        Returns:
            {
                'orb_high': float,
                'orb_low': float,
                'orb_midpoint': float,
                'orb_range_pct': float,
                'volume': int
            }
        """
        # Fetch 1-minute bars for today
        hist = ticker_obj.history(period='1d', interval='1m')
        
        if hist.empty:
            raise ValueError("No intraday data available")
        
        # Filter to 14:30-14:45 UTC window
        today = datetime.now(timezone.utc).date()
        orb_start = datetime.combine(today, datetime.min.time()).replace(
            hour=14, minute=30, tzinfo=timezone.utc
        )
        orb_end = datetime.combine(today, datetime.min.time()).replace(
            hour=14, minute=45, tzinfo=timezone.utc
        )
        
        orb_data = hist.loc[orb_start:orb_end]
        
        if orb_data.empty:
            raise ValueError(f"No data in ORB window {orb_start} - {orb_end}")
        
        orb_high = float(orb_data['High'].max())
        orb_low = float(orb_data['Low'].min())
        orb_midpoint = (orb_high + orb_low) / 2
        orb_range = orb_high - orb_low
        orb_range_pct = (orb_range / orb_high) * 100
        volume = int(orb_data['Volume'].sum())
        
        return {
            'orb_high': orb_high,
            'orb_low': orb_low,
            'orb_midpoint': orb_midpoint,
            'orb_range_pct': orb_range_pct,
            'volume': volume
        }
    
    @staticmethod
    def calculate_atr(ticker_obj: yf.Ticker, period: int = 14) -> float:
        """Calculate 14-period Average True Range"""
        hist = ticker_obj.history(period='1mo', interval='1d')
        
        if len(hist) < period:
            raise ValueError(f"Insufficient data for ATR ({len(hist)} < {period})")
        
        high_low = hist['High'] - hist['Low']
        high_close = abs(hist['High'] - hist['Close'].shift())
        low_close = abs(hist['Low'] - hist['Close'].shift())
        
        true_range = high_low.combine(high_close, max).combine(low_close, max)
        atr = float(true_range.rolling(window=period).mean().iloc[-1])
        
        return atr
    
    @staticmethod
    def get_latest_5m_close(ticker_obj: yf.Ticker) -> Tuple[float, datetime]:
        """
        Get most recent 5m candle CLOSE price.
        Strategy triggers on CANDLE CLOSE, not live price.
        """
        hist = ticker_obj.history(period='1d', interval='5m')
        
        if hist.empty:
            raise ValueError("No 5m candle data")
        
        latest_candle = hist.iloc[-1]
        close_price = float(latest_candle['Close'])
        close_time = latest_candle.name.to_pydatetime()
        
        return close_price, close_time


class AntiTrapFilter:
    """Pre-trade validation filters to reject trap setups"""
    
    MIN_VOLUME_MULTIPLIER = 1.5  # 150% of average
    MAX_RANGE_PCT = 2.5  # Reject if ORB range > 2.5%
    MAX_SPREAD_PCT = 0.15  # Liquidity guard
    
    @staticmethod
    def check_volume(current_volume: int, avg_volume_20d: int) -> Tuple[bool, str]:
        """Volume must be > 150% of 20-day average"""
        if current_volume < avg_volume_20d * AntiTrapFilter.MIN_VOLUME_MULTIPLIER:
            return False, f"Volume {current_volume:,} < {AntiTrapFilter.MIN_VOLUME_MULTIPLIER}x avg ({avg_volume_20d:,})"
        return True, ""
    
    @staticmethod
    def check_range_cap(orb_range_pct: float) -> Tuple[bool, str]:
        """Reject if ORB range too wide (indicates gap/volatility)"""
        if orb_range_pct > AntiTrapFilter.MAX_RANGE_PCT:
            return False, f"Range {orb_range_pct:.2f}% > {AntiTrapFilter.MAX_RANGE_PCT}% (TOO WIDE)"
        return True, ""
    
    @staticmethod
    def check_spread(bid: float, ask: float) -> Tuple[bool, str]:
        """Spread must be < 0.15% for liquidity"""
        mid = (bid + ask) / 2
        spread_pct = ((ask - bid) / mid) * 100
        
        if spread_pct > AntiTrapFilter.MAX_SPREAD_PCT:
            return False, f"Spread {spread_pct:.2f}% > {AntiTrapFilter.MAX_SPREAD_PCT}%"
        return True, ""
    
    @staticmethod
    def check_recoil_trap(current_price: float, orb_midpoint: float, orb_high: float) -> Tuple[bool, str]:
        """
        Recoil Trap: If price closes below midpoint within 10 mins of breakout,
        position should be liquidated. This is a POST-entry check.
        """
        if current_price < orb_midpoint:
            return False, f"RECOIL TRAP: ${current_price:.2f} < midpoint ${orb_midpoint:.2f}"
        return True, ""


class JobCScalper:
    """Main 15m ORB Scalper with Zombie Recovery"""
    
    def __init__(self, watch_list: List[str], dry_run: bool = True):
        self.watch_list = watch_list
        self.dry_run = dry_run
        
        # Clients
        self.client = Trading212Client()
        self.auditor = TradingAuditor()
        
        # Signal handler for SIGTERM (from orb_shield.py)
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        
        print(f"\n{'='*70}")
        print(f"🎯 JOB C SCALPER v1.9.1")
        print(f"{'='*70}")
        print(f"⏰ Execution time: {datetime.now(timezone.utc).isoformat()}")
        print(f"📊 Watch list: {', '.join(watch_list)}")
        print(f"🧪 Dry run: {'ENABLED' if dry_run else 'DISABLED (LIVE TRADING)'}")
        print(f"{'='*70}\n")
    
    def handle_sigterm(self, signum, frame):
        """Handle SIGTERM from orb_shield.py"""
        print("\n🛑 SIGTERM received from ORB Shield. Emergency shutdown...")
        sys.exit(0)
    
    def load_instruments_db(self) -> Dict:
        """Load instruments.json for ticker validation"""
        try:
            with open('data/instruments.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  data/instruments.json not found. Run build_universe.py first.")
            return {'instruments': []}
    
    def validate_ticker(self, ticker: str, instruments_db: Dict) -> bool:
        """Validate ticker exists in instruments database"""
        instruments = instruments_db.get('instruments', [])
        ticker_list = [i['ticker'] for i in instruments]
        
        if ticker not in ticker_list:
            print(f"❌ {ticker} not in instruments database")
            return False
        return True
    
    def execute_trade(self, ticker: str, quantity: int, limit_price: float) -> bool:
        """Execute limit order via Trading 212"""
        if self.dry_run:
            print(f"   🧪 [DRY RUN] Would place order: {ticker} {quantity} @ ${limit_price:.2f}")
            return True
        
        try:
            order = self.client.place_limit_order(
                ticker=ticker,
                quantity=quantity,
                limit_price=limit_price,
                side='BUY'
            )
            print(f"   ✅ ORDER PLACED: {order.get('id', 'unknown')}")
            return True
        except Exception as e:
            print(f"   ❌ ORDER FAILED: {e}")
            return False
    
    def log_theoretical_signal(self, ticker: str, orb_metrics: Dict):
        """Log theoretical signal when data is stale"""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
            'ticker': ticker,
            'orb_high': orb_metrics['orb_high'],
            'orb_low': orb_metrics['orb_low'],
            'status': 'STALE_DATA_NO_TRADE'
        }
        
        os.makedirs('data/logs', exist_ok=True)
        with open('data/logs/theoretical_signals.json', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        print(f"   📝 Theoretical signal logged to data/logs/theoretical_signals.json")
    
    def process_ticker(self, ticker: str, instruments_db: Dict):
        """Process single ticker through full ORB strategy"""
        print(f"\n{'─'*70}")
        print(f"📊 Processing: {ticker}")
        print(f"{'─'*70}")
        
        # Step 1: Ticker validation
        if not self.validate_ticker(ticker, instruments_db):
            return
        
        # Step 2: Pre-flight data fetch (14:25 UTC check)
        print("⏳ Attempting data fetch...")
        recovery = ZombieRecovery(ticker)
        ticker_obj = recovery.fetch_intraday_data()
        
        # Step 3: Zombie Recovery if needed
        if not ticker_obj:
            print("❌ Pre-flight FAILED. Entering Zombie Recovery...\n")
            ticker_obj, is_stale = recovery.enter_retry_loop()
            
            if not ticker_obj:
                print(f"❌ Zombie Recovery FAILED permanently for {ticker}\n")
                return
            
            if is_stale:
                # Calculate retrospective ORB for logging only
                try:
                    orb_metrics = ORBEngine.calculate_orb_retrospective(ticker_obj)
                    self.log_theoretical_signal(ticker, orb_metrics)
                except Exception as e:
                    print(f"❌ ORB calculation failed: {e}")
                return
        
        # Step 4: Calculate ORB metrics (retrospective if recovered)
        try:
            orb_metrics = ORBEngine.calculate_orb_retrospective(ticker_obj)
            atr = ORBEngine.calculate_atr(ticker_obj)
            
            print(f"✅ ORB Metrics:")
            print(f"   High: ${orb_metrics['orb_high']:.2f}")
            print(f"   Low: ${orb_metrics['orb_low']:.2f}")
            print(f"   Midpoint: ${orb_metrics['orb_midpoint']:.2f}")
            print(f"   Range: {orb_metrics['orb_range_pct']:.2f}%")
            print(f"   Volume: {orb_metrics['volume']:,}")
            print(f"   ATR(14): ${atr:.2f}")
            
        except Exception as e:
            print(f"❌ ORB calculation failed: {e}\n")
            return
        
        # Step 5: Get latest 5m candle CLOSE
        try:
            close_price, close_time = ORBEngine.get_latest_5m_close(ticker_obj)
            print(f"\n💰 Latest 5m Close: ${close_price:.2f} @ {close_time.strftime('%H:%M:%S')} UTC")
        except Exception as e:
            print(f"❌ Failed to get 5m close: {e}\n")
            return
        
        # Step 6: Check for breakout (CLOSE above ORB High)
        if close_price <= orb_metrics['orb_high']:
            print(f"⏸️  No breakout: ${close_price:.2f} <= ORB High ${orb_metrics['orb_high']:.2f}\n")
            return
        
        print(f"🚀 BREAKOUT DETECTED: ${close_price:.2f} > ${orb_metrics['orb_high']:.2f}")
        
        # Step 7: Anti-trap filters
        print("\n🛡️  Running anti-trap filters...")
        
        # Volume check (TODO: Fetch real 20-day avg from ticker_obj)
        avg_volume_20d = 5000000  # Placeholder
        passed, reason = AntiTrapFilter.check_volume(orb_metrics['volume'], avg_volume_20d)
        if not passed:
            print(f"   ❌ REJECTED: {reason}\n")
            return
        print(f"   ✅ Volume check passed")
        
        # Range cap check
        passed, reason = AntiTrapFilter.check_range_cap(orb_metrics['orb_range_pct'])
        if not passed:
            print(f"   ❌ REJECTED: {reason}\n")
            return
        print(f"   ✅ Range cap check passed")
        
        # Spread check (TODO: Fetch real bid/ask from Trading 212 API)
        bid, ask = close_price * 0.999, close_price * 1.001  # Placeholder
        passed, reason = AntiTrapFilter.check_spread(bid, ask)
        if not passed:
            print(f"   ❌ REJECTED: {reason}\n")
            return
        print(f"   ✅ Spread check passed")
        
        # Step 8: Calculate entry and stop
        target_entry = orb_metrics['orb_high'] + (0.1 * atr)
        stop_loss = orb_metrics['orb_high'] - (1.5 * atr)
        
        print(f"\n📍 Trade Levels:")
        print(f"   Target Entry: ${target_entry:.2f}")
        print(f"   Stop Loss: ${stop_loss:.2f}")
        print(f"   Risk/Reward: {((target_entry - close_price) / (close_price - stop_loss)):.2f}x")
        
        # Step 9: Seed Rule position sizing
        max_position = self.auditor.get_seed_rule_limit()
        quantity = int(max_position / target_entry)
        
        print(f"\n💵 Position Sizing:")
        print(f"   Max position: £{max_position:.2f} (Seed Rule)")
        print(f"   Quantity: {quantity} shares")
        print(f"   Notional: £{quantity * target_entry:.2f}")
        
        # Step 10: Execute trade
        print(f"\n🎯 Executing trade...")
        success = self.execute_trade(ticker, quantity, target_entry)
        
        if success:
            print(f"✅ {ticker} trade complete\n")
        else:
            print(f"❌ {ticker} trade failed\n")
    
    def run(self):
        """Main execution loop"""
        # Load instruments database
        instruments_db = self.load_instruments_db()
        
        # Process each ticker in watch list
        for ticker in self.watch_list:
            self.process_ticker(ticker, instruments_db)
        
        print(f"\n{'='*70}")
        print(f"✅ JOB C SCALPER SESSION COMPLETE")
        print(f"⏰ End time: {datetime.now(timezone.utc).isoformat()}")
        print(f"{'='*70}\n")


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Job C Scalper v1.9.1')
    parser.add_argument('--live', action='store_true', help='Live trading mode (default: dry run)')
    parser.add_argument('--tickers', nargs='+', default=['NVDA', 'TSLA', 'AMD'], 
                       help='Tickers to watch (default: NVDA TSLA AMD)')
    
    args = parser.parse_args()
    
    scalper = JobCScalper(
        watch_list=args.tickers,
        dry_run=not args.live
    )
    
    try:
        scalper.run()
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")


if __name__ == '__main__':
    main()
