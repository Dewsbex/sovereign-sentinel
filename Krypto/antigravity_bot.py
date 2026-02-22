#!/usr/bin/env python3
"""
Sovereign Sentinel: Antigravity Strategy Engine (Job D)
Identifies 4-Hour institutional "Trap Door" sweeps and executes on reclaiming the baseline.
Isolated £2000 Ledger.
"""

import sys
import os
import time
import json
import datetime
import yfinance as yf
from trading212_client import Trading212Client
from telegram_bot import SovereignAlerts
from audit_log import AuditLogger

JOB_ID = "SS012-Antigravity"
LEDGER_FILE = 'data/antigravity_ledger.json'
UNIVERSE_FILE = 'data/master_universe.json'
MAX_ALLOCATION = 2000.00
RISK_PER_TRADE = 0.50 # 50% of available ledger cash per trade signal

class AntigravityBot:
    def __init__(self):
        self.logger = AuditLogger(JOB_ID)
        self.logger.log("STARTUP", "System", "Initializing Antigravity Engine...", "INFO")
        self.client = Trading212Client()
        self.alerts = SovereignAlerts()
        
        # Determine current available funds
        self.ledger = self._load_ledger()
        
    def _load_ledger(self):
        """Loads or creates the isolated £2000 ledger."""
        if not os.path.exists(LEDGER_FILE):
            default_ledger = {
                "initial_funding": MAX_ALLOCATION,
                "current_cash": MAX_ALLOCATION,
                "realized_profit": 0.0,
                "history": []
            }
            with open(LEDGER_FILE, 'w') as f:
                json.dump(default_ledger, f)
            return default_ledger
            
        with open(LEDGER_FILE, 'r') as f:
            return json.load(f)

    def _update_ledger(self, pnl, trade_notes=""):
        """Updates the ledger with realized PNL."""
        self.ledger["current_cash"] += pnl
        self.ledger["realized_profit"] += pnl
        self.ledger["history"].append({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "pnl": pnl,
            "notes": trade_notes
        })
        with open(LEDGER_FILE, 'w') as f:
            json.dump(self.ledger, f, indent=4)
            
    def get_valid_universe(self):
        """Loads target list, enforcing US-only and ISA-compliant rules."""
        if not os.path.exists(UNIVERSE_FILE):
            self.logger.log("DATA_ERROR", "System", f"Missing {UNIVERSE_FILE}", "CRITICAL")
            return []
            
        with open(UNIVERSE_FILE, 'r') as f:
            data = json.load(f)
            
        targets = []
        for inst in data.get('instruments', []):
            ticker = inst.get('ticker', '')
            # Filter Rules:
            is_uk = ticker.endswith('.L')
            is_isa = inst.get('isa', False)
            
            if not is_uk and is_isa:
                # IMPORTANT: We must resolve the hardcoded master_universe string 
                # against the LIVE Trading 212 instruments list to get the real underlying ticker 
                # (to prevent yfinance crashing on tickers that mapped differently like $SQ)
                real_ticker, yf_ticker, inst_data = self.client.resolve_ticker(ticker)
                if real_ticker:
                    inst['yf_ticker'] = yf_ticker
                    inst['t212_ticker'] = real_ticker
                    targets.append(inst)
                
        return targets

    def is_earnings_imminent(self, ticker):
        """Checks if earnings are within 72 hours (yfinance best effort)."""
        try:
            t = yf.Ticker(ticker)
            calendar = t.calendar
            if calendar is not None and not calendar.empty:
                # yfinance calendar format changed recently, checking both standard structures
                if 'Earnings Date' in calendar.index:
                    earliest = calendar.loc['Earnings Date'].iloc[0]
                else: 
                    # Try accessing as columns if it's a dataframe
                    earliest = calendar.iloc[0, 0] if not calendar.empty else None

                if earliest:
                    try:
                        # Convert to timezone naive if needed
                        if hasattr(earliest, 'tz_localize'):
                            earliest = earliest.tz_localize(None)
                        now = datetime.datetime.now()
                        diff = earliest - now
                        if datetime.timedelta(days=0) <= diff <= datetime.timedelta(days=3):
                            return True
                    except:
                        pass
        except Exception as e:
            self.logger.log("EARNINGS_CHECK_ERROR", ticker, str(e), "WARNING")
        
        return False
        
    def check_sector_health(self, sector_name):
        """Ensures the broader sector is not dragging down > 2%."""
        sector_etfs = {
            "Semiconductors": "SMH",
            "Autos/AI": "XLY",
            "Software/Crypto": "IGV",
            "Memory": "SMH",
            "Foundry": "SMH",
            "Cyber": "HACK",
            "Cloud": "SKYY",
            "Data Center": "SKYY"
        }
        
        etf_ticker = sector_etfs.get(sector_name, "SPY") # Fallback to SPY
        try:
            t = yf.Ticker(etf_ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[0]
                curr_price = hist['Close'].iloc[1]
                pct_change = (curr_price - prev_close) / prev_close
                if pct_change < -0.02:
                    return False, f"{etf_ticker} down {pct_change:.2%}"
        except:
            pass # Fail open if ETF data errors out
            
        return True, "Healthy"

    def scan_for_trap_door(self, ticker):
        """
        Analyzes 4-Hour timeframe for Institutional Sweeps.
        Logic: Swing low (lower than 3 prior and 3 post), price drops into Strike Zone (Baseline - 0.5 ATR), 
        and latest completed candle closes BACK ABOVE the Baseline.
        """
        try:
            t = yf.Ticker(ticker)
            # Need at least 20 periods for ATR 14, plus 3 post-candles for swing confirmation.
            df = t.history(period="10d", interval="4h")
            if len(df) < 20: 
                return None
                
            # Calculate ATR (14)
            df['H-L'] = df['High'] - df['Low']
            df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
            df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
            df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
            df['ATR'] = df['TR'].rolling(window=14).mean()
            
            # Find recent Swing Lows
            for i in range(len(df) - 4, 14, -1): # Start 1 candle back from current (which is forming) to 14 periods deep
                is_swing_low = True
                current_low = df['Low'].iloc[i]
                
                # Check 3 preceding and 3 following
                for j in range(1, 4):
                    if df['Low'].iloc[i-j] <= current_low or df['Low'].iloc[i+j] <= current_low:
                        is_swing_low = False
                        break
                        
                if is_swing_low:
                    baseline = current_low
                    atr = df['ATR'].iloc[i]
                    strike_zone_bottom = baseline - (0.5 * atr)
                    
                    # Ensure the candle's wick explicitly swept the Strike Zone
                    if float(current_low) <= float(strike_zone_bottom):
                        # The Reclaim Check: Did the most recently *completed* 4H candle close above baseline?
                        # Using [-2] because [-1] is the currently forming candle.
                        last_closed = df['Close'].iloc[-2]
                        
                        if float(last_closed) > float(baseline):
                            # Ensure we aren't chasing a move that already blasted off
                            sma20 = df['Close'].rolling(window=20).mean().iloc[-2]
                            if float(last_closed) < float(sma20):
                                return {
                                    "baseline": baseline,
                                    "sweep_low": current_low,
                                    "sma20": sma20,
                                    "current_price": df['Close'].iloc[-1]
                                }
            return None
        except Exception as e:
            self.logger.log("SCAN_ERROR", ticker, str(e), "ERROR")
            return None

    def execute_strategy(self):
        """Runs the Antigravity workflow."""
        available_cash = self.ledger.get('current_cash', 0.0)
        if available_cash < 50.0:
            self.logger.log("LEDGER_EMPTY", "System", f"Available funds too low: £{available_cash}", "WARNING")
            return

        universe = self.get_valid_universe()
        self.logger.log("SCAN_START", "System", f"Scanning {len(universe)} targets for 4H Trap Doors.", "INFO")
        
        # Guard to prevent spamming orders if we already have positions
        # Technically we should track open orders, but for v1 we'll limit to 1 active execution per run
        executions_this_run = 0

        for inst in universe:
            if executions_this_run > 0:
                break
                
            yf_ticker = inst['yf_ticker']
            t212_ticker = inst['t212_ticker']
            sector = inst.get('sector', 'Unknown')
            
            signal = self.scan_for_trap_door(yf_ticker)
            if signal:
                self.logger.log("SWEEP_DETECTED", yf_ticker, f"Baseline: {signal['baseline']:.2f}")
                
                if self.is_earnings_imminent(yf_ticker):
                    self.logger.log("EARNINGS_BLOCK", yf_ticker, "Earnings within 72h. Skipping.", "WARNING")
                    continue
                    
                is_healthy, reason = self.check_sector_health(sector)
                if not is_healthy:
                    self.logger.log("SECTOR_BLOCK", yf_ticker, f"Sector Weak: {reason}", "WARNING")
                    continue
                
                # Validation passed. Position sizing.
                trade_cash = min(available_cash * RISK_PER_TRADE, available_cash)
                qty = self.client.calculate_max_buy(t212_ticker, trade_cash, signal['current_price'])
                
                if qty <= 0:
                    continue

                # STRIKE PROTOCOL
                self.logger.log("BUY_SIGNAL", t212_ticker, f"Reclaim Confirmed. Executing...", "SUCCESS")
                
                # 1. Market Buy
                buy_res = self.client.place_market_order(t212_ticker, qty, extended_hours=True)
                if buy_res.get('status') == 'FAILED':
                    self.logger.log("ORDER_FAIL", t212_ticker, f"Buy Failed: {buy_res.get('error')}", "ERROR")
                    continue
                    
                time.sleep(2) # Prevent Rate Limit
                
                # 2. Hard Stop Loss (Negative Qty for Sell)
                stop_price = signal['sweep_low'] - 0.01
                stop_res = self.client.place_stop_order(t212_ticker, -qty, stop_price)
                if stop_res.get('status') == 'FAILED':
                    self.logger.log("STOP_FAIL", t212_ticker, f"Stop Loss Failed: {stop_res.get('error')}", "CRITICAL")
                
                time.sleep(2)
                
                # 3. Take Profit Limit (Negative Qty for Sell)
                limit_res = self.client.place_limit_order(t212_ticker, -qty, signal['sma20'], side='SELL')
                if limit_res.get('status') == 'FAILED':
                    self.logger.log("LIMIT_FAIL", t212_ticker, f"Take Profit Failed: {limit_res.get('error')}", "ERROR")
                
                # Update Ledger state
                self._update_ledger(0.0, f"Executed trade for {qty} {t212_ticker} at ~{signal['current_price']}")
                
                msg = f"🛸 **ANTIGRAVITY STRIKE**\n" \
                      f"**Ticker**: `{t212_ticker}`\n" \
                      f"**Sweep Low**: ${signal['sweep_low']:.2f}\n" \
                      f"**Baseline Reclaimed**: ${signal['baseline']:.2f}\n" \
                      f"**Stop-Loss**: ${stop_price:.2f}\n" \
                      f"**Take-Profit**: ${signal['sma20']:.2f}\n" \
                      f"**Ledger Cash**: £{self.ledger['current_cash']:.2f}"
                self.alerts.send_message(msg)
                
                executions_this_run += 1
                
        self.logger.log("SCAN_COMPLETE", "System", f"Finished scanning. Executions: {executions_this_run}", "SUCCESS")

if __name__ == "__main__":
    bot = AntigravityBot()
    bot.execute_strategy()
