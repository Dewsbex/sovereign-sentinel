import json
import os
import yfinance as yf
import pandas as pd
from trading212_client import Trading212Client
from ledger import SessionLedger

class SniperStrategy:
    """The Muscle: Analysis and Risk Management logic."""
    
    def __init__(self, client: Trading212Client):
        self.client = client
        self.targets_file = 'data/targets.json'
        self.ledger = SessionLedger()
        self.triggered_today = set() # Track executed tickers in memory
        self.last_scan_date = None

    def scan_market(self):
        """Loads targets and checks for breakout (One-shot per day per ticker)"""
        # Reset local cache if new day
        from datetime import datetime
        today = datetime.utcnow().date()
        if self.last_scan_date != today:
            self.triggered_today.clear()
            self.last_scan_date = today

        if not os.path.exists(self.targets_file):
            return []
            
        # FRESHNESS CHECK
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(self.targets_file)).date()
        if file_mod_time < today:
            print(f"Targets Stale ({file_mod_time}). Waiting for Morning Brief...")
            return []
            
        with open(self.targets_file, 'r') as f:
            targets = json.load(f)
            
        triggers = []
        # Batch fetch for speed
        # Check both local memory and persistent ledger
        tickers_to_scan = [
            t['ticker'] for t in targets 
            if t['ticker'] not in self.triggered_today and not self.ledger.is_job_c_holding(t['ticker'])
        ]
        
        if not tickers_to_scan:
            return []
            
        try:
            # Silent batch fetch
            data = yf.download(tickers_to_scan, period="1d", interval="1m", progress=False, group_by='ticker')
            
            for target in targets:
                ticker = target['ticker']
                if ticker in self.triggered_today or self.ledger.is_job_c_holding(ticker):
                    continue
                    
                trigger_price = target['trigger_price']
                
                # Extract current price
                try:
                    if len(tickers_to_scan) > 1:
                        # Handle MultiIndex: data[ticker]['Close'] or data[('Close', ticker)]
                        try:
                            # ZOMBIE CHECK (v2.1)
                            # Get the last row
                            row = data[ticker].iloc[-1]
                            timestamp = row.name
                            price = row['Close']
                        except:
                            # Fallback for weird yf structures
                            if (ticker, 'Close') in data.columns:
                                row = data[ticker].iloc[-1] # This might be wrong index wise if flat
                                # simplified:
                                price = data[(ticker, 'Close')].iloc[-1]
                                timestamp = data.index[-1]
                            elif ('Close', ticker) in data.columns:
                                price = data[('Close', ticker)].iloc[-1]
                                timestamp = data.index[-1]
                            else:
                                continue
                    else:
                        row = data.iloc[-1]
                        price = row['Close']
                        timestamp = row.name
                        
                    if pd.isna(price): continue

                    # Execute Zombie Check
                    # Convert pandas timestamp to python datetime (UTC)
                    if hasattr(timestamp, 'to_pydatetime'):
                        ts_dt = timestamp.to_pydatetime()
                    else:
                        ts_dt = timestamp

                    # Ensure tz-naive for comparison (assuming UTC system)
                    if ts_dt.tzinfo:
                        ts_dt = ts_dt.replace(tzinfo=None) # yf is UTC usually
                    
                    now_utc = datetime.utcnow()
                    staleness = (now_utc - ts_dt).total_seconds()
                    
                    # Rulebook Limit: 900 seconds (15 minutes) to accommodate yfinance feed latency
                    if staleness > 900: 
                         # We log it but potentially allow if it's exactly 15m (delayed feed)? 
                         # No, Rulebook says "Voided".
                         print(f"🧟 ZOMBIE REJECTION: {ticker} data is {staleness:.0f}s old (>900s).")
                         continue

                    # v2.5 APROMS: 15m Breakout + 5m Candle Close Confirmation
                    # v2.2 UPDATE: State-Driven "Buy Zone" (Trigger to 1% Slack)
                    SLACK_PCT = 0.01
                    SLACK_LIMIT = trigger_price * (1 + SLACK_PCT)
                    
                    if trigger_price <= price <= SLACK_LIMIT:
                        # CHECK 5M CONFIRMATION
                        try:
                            # Fetch 5m candles for the last 15 mins
                            df_5m = yf.download(ticker, period="1d", interval="5m", progress=False)
                            if df_5m.empty: continue
                            
                            # Confirmation Logic: The previous full 5m candle MUST have closed above the trigger.
                            # This prevents buying a 'wick' cross that immediately fails.
                            last_full_5m_close_series = df_5m['Close'].iloc[-2] # Previous 5m candle close
                            
                            # Handle potential Series if yf returns weird MultiIndex structures
                            if hasattr(last_full_5m_close_series, 'iloc'):
                                last_full_5m_close = float(last_full_5m_close_series.iloc[-1])
                            else:
                                last_full_5m_close = float(last_full_5m_close_series)
                            
                            if last_full_5m_close > float(trigger_price):
                                print(f"🔱 CONFIRMATION GAUNTLET PASSED: {ticker} Previous 5m Close ${last_full_5m_close:.2f} > ${trigger_price}")
                            else:
                                print(f"⏳ CONFIRMATION PENDING: {ticker} at ${price:.2f} but previous 5m candle closed BELOW trigger (${last_full_5m_close:.2f})")
                                continue
                        except Exception as e:
                            print(f"Confirmation Error {ticker}: {e}")
                            # Fail safe: require confirmation
                            continue

                        print(f"BREAKOUT CONFIRMED: {ticker} ${price:.2f} (In {SLACK_PCT*100}% Buy Zone)")
                        self.triggered_today.add(ticker)
                        triggers.append({
                            'ticker': ticker,
                            'quantity': target['quantity'],
                            'price': price,
                            'stop_loss': target['stop_loss'],
                            'timestamp': timestamp # identifying data age
                        })
                    elif price > SLACK_LIMIT:
                        print(f"🚫 OVEREXTENDED: {ticker} at ${price:.2f} is > {SLACK_PCT*100}% above trigger (${trigger_price:.2f}).")
                except Exception as e:
                    # print(f"Scan Error {ticker}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Scan Batch Error: {e}")
                
        return triggers
        
    def check_risk_rules(self):
        """Checks open positions for Stop Loss / Take Profit"""
        try:
            # 🛡️ IRON ISOLATION: Import Session Manager for whitelist enforcement
            from session_manager import SessionManager
            session_mgr = SessionManager()
            
            positions = self.client.get_positions()
            exits = []
            
            # Load targets for stop loss values
            if not os.path.exists(self.targets_file):
                return []
                
            with open(self.targets_file, 'r') as f:
                targets_list = json.load(f)
                targets = {t['ticker']: t for t in targets_list}
            
            for pos in positions:
                ticker = pos['ticker']
                
                # 🛡️ IRON ISOLATION: Only check positions bought THIS SESSION
                # This prevents Job C from managing risk on strategic holdings (Job A)
                if not session_mgr.is_whitelisted(ticker):
                    # This is a strategic holding or pre-existing position
                    # Job C has NO AUTHORITY to touch it
                    print(f"PROTECTED HOLDING: {ticker} skipped (not in session whitelist)")
                    continue
                
                # T212 might return ticker without suffix, but our targets use raw ticker
                # We check both just in case
                lookup_ticker = ticker
                if lookup_ticker not in targets and "_" in ticker:
                     lookup_ticker = ticker.split("_")[0]

                if lookup_ticker in targets:
                    target_data = targets[lookup_ticker]
                    stop_loss = target_data.get('stop_loss')
                    
                    # Entry Price (Average Price from Broker)
                    avg_price = float(pos.get('averagePrice', 0))
                    current_price = float(pos['currentPrice'])
                    quantity = float(pos['quantity'])
                    
                    # 1. STOP LOSS CHECK
                    if stop_loss and current_price < stop_loss:
                        print(f"STOP LOSS TRIGGERED: {lookup_ticker} (${current_price:.2f} < ${stop_loss})")
                        exits.append({
                            'ticker': lookup_ticker,
                            'quantity': quantity,
                            'price': current_price,
                            'reason': 'STOP_LOSS'
                        })
                        continue

                    # 2. TAKE PROFIT CHECK (2:1 Reward Logic)
                    # Risk = Entry - Stop
                    # Target = Entry + (2 * Risk)
                    if stop_loss and avg_price > stop_loss:
                        risk_per_share = avg_price - stop_loss
                        take_profit_price = avg_price + (2 * risk_per_share)
                        
                        if current_price >= take_profit_price:
                             print(f"TAKE PROFIT TRIGGERED: {lookup_ticker} (${current_price:.2f} >= ${take_profit_price:.2f})")
                             exits.append({
                                'ticker': lookup_ticker,
                                'quantity': quantity,
                                'price': current_price,
                                'reason': 'TAKE_PROFIT_2R'
                             })
                             
            return exits
        except Exception as e:
            print(f"Risk Error: {e}")
            return []
