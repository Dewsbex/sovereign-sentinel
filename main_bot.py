import yfinance as yf
import requests
import time
import os
import sys
from datetime import datetime

# Set stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Titan Shield Integration
try:
    import orb_sidecar
except ImportError:
    print("❌ Critical Error: Titan Shield (orb_sidecar.py) not found!")
    sys.exit(1)

# --- Configuration ---
T212_API_KEY = os.environ.get("T212_API_KEY")
BASE_URL = "https://live.trading212.com/api/v0/equity"
HEADERS = {"Authorization": T212_API_KEY} if T212_API_KEY else {}

# Watchlist for ORB (Example Universe)
WATCHLIST = ["TSLA", "NVDA", "AAPL", "AMD", "MSFT", "AMZN", "META", "GOOGL"]

# --- Phase 1: Targeting ---
def get_orb_targets(ticker_list):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 Scanning Market for High RVOL Targets...")
    targets = []
    for ticker in ticker_list:
        try:
            data = yf.Ticker(ticker)
            # Fetch 10 days history
            hist = data.history(period="10d")
            if hist.empty: continue
            
            avg_vol = hist['Volume'].mean()
            
            # Use 'regularMarketVolume' if available, else last volume from history
            current_vol = data.info.get('regularMarketVolume', 0)
            if current_vol == 0 and not hist.empty:
                 current_vol = hist['Volume'].iloc[-1]

            rvol = current_vol / avg_vol if avg_vol > 0 else 0
            
            if rvol > 1.5:
                print(f"   🔥 {ticker} Identified! RVOL: {rvol:.2f}")
                targets.append(ticker)
            else:
                # Debug print for low volume
                # print(f"   . {ticker} RVOL: {rvol:.2f}")
                pass
                
        except Exception as e:
            print(f"   ⚠️ Error scanning {ticker}: {e}")
            
    return targets

# --- Phase 3 & 4: Risk & Slippage Audit ---
def execution_audit(trigger_price, fill_price):
    if trigger_price == 0: return False
    
    # Slippage Tax calculation
    slippage = (fill_price - trigger_price) / trigger_price
    
    print(f"   ⚖️ Audit: Trigger {trigger_price} vs Fill {fill_price} (Slippage: {slippage:.2%})")
    
    if abs(slippage) > 0.002: # 0.2% Kill-switch
        print(f"   🛑 CRITICAL SLIPPAGE: {slippage:.2%}. Thread Aborted.")
        return False # Triggers immediate market exit
    return True

# --- Phase 2: Synthetic Limit Engine ---
class SyntheticLimitEngine:
    def __init__(self, ticker, range_high, range_low, capital_limit):
        self.ticker = ticker
        self.range_high = range_high
        self.range_low = range_low
        self.triggered = False
        self.capital_limit = capital_limit
        self.position = None # Store position details

    def execute_trade(self, side, price):
        print(f"   ⚡ TRIGGER FIRED: {side} {self.ticker} @ {price}")
        
        # 1. Titan Shield Check
        # Calculate quantity based on limit. 
        # For simplicity in this v1, we allocate the FULL capital limit to this trade
        qty = self.capital_limit / price
        
        # Check explicit limit (Redundant but safe)
        trade_value = qty * price
        allowed, safe_value, reason = orb_sidecar.check_strategy_limit(trade_value, self.capital_limit)
        
        if not allowed:
            print(f"   🛡️ Titan Shield Intervened: {reason}")
            # Recalculate Qty
            qty = safe_value / price
            
        print(f"   🚀 Sending MARKET Order: {qty:.4f} shares (~£{safe_value:.2f})...")
        
        # API CALL WOULD GO HERE
        # response = requests.post(f"{BASE_URL}/orders", json={...}, headers=HEADERS)
        # Assuming fill at current price for simulation
        fill_price = price 
        
        # 2. Execution Audit
        if execution_audit(price, fill_price):
            self.triggered = True
            self.position = {
                "side": side,
                "entry": fill_price,
                "shares": qty,
                "stop": self.range_low if side == "BUY" else self.range_high,
                "target": price + (2 * (self.range_high - self.range_low)) if side == "BUY" else price - (2 * (self.range_high - self.range_low))
            }
            print(f"   ✅ Position Open: Target {self.position['target']:.2f} | Stop {self.position['stop']:.2f}")

    def on_tick(self, current_price):
        if self.triggered: 
            # Phase 5: Management (Check Target/Stop)
            if self.position:
                if self.position['side'] == "BUY":
                    if current_price >= self.position['target']:
                        print(f"   🎯 TARGET HIT: {self.ticker} @ {current_price}. Closing.")
                        self.position = None # Close
                    elif current_price <= self.position['stop']:
                        print(f"   🛑 STOP HIT: {self.ticker} @ {current_price}. Closing.")
                        self.position = None # Close
            return

        print(f"   👀 Watching {self.ticker}: {current_price:.2f} (H: {self.range_high} | L: {self.range_low})", end='\r')

        # Buy Trigger
        if current_price >= self.range_high + 0.01:
            print("") # Newline
            self.execute_trade(side="BUY", price=current_price)
            
        # Sell Trigger (Inverse ETP or Shorting if allowed - assuming Long Only for ISA usually, but logic stands)
        # Note: ISA Accounts cannot short. Assuming Long Only for now or Inverse ETPs.
        # Keeping logic generic.
        elif current_price <= self.range_low - 0.01:
            print("")
            print(f"   📉 Short Signal (Low Break) for {self.ticker} - Skipping (ISA Context)")
            # self.execute_trade(side="SELL", price=current_price) 


# --- Main Bot Loop ---
def run_orb_session():
    print("🤖 ORB Bot v32.14: Initializing Session...")
    
    # 1. Load Strategy Capital Ceiling
    config = orb_sidecar.load_config()
    STRATEGY_CAP = float(config.get("STRATEGY_CAP_GBP", 500.0))
    print(f"💰 Titan Shield Active. Hard Deck: £{STRATEGY_CAP:.2f}")
    
    # 2. Targeting
    targets = get_orb_targets(WATCHLIST)
    if not targets:
        print("😴 No valid targets found today. Shutting down.")
        return

    # 3. Setup Engines
    engines = []
    # Mocking range data for simulation since we aren't live at 14:30
    # In production, you'd fetch the first 15m candle high/low here.
    for t in targets:
        # Fetch current price to establish mock range
        data = yf.Ticker(t)
        current = data.fast_info['last_price']
        range_high = current * 1.005
        range_low = current * 0.995
        
        eng = SyntheticLimitEngine(t, range_high, range_low, STRATEGY_CAP)
        engines.append(eng)
        print(f"   ⚙️ Engine Armed: {t} [H: {range_high:.2f}, L: {range_low:.2f}]")

    print("\n⏳ Entering High-Frequency Loop (Simulated)... Press Ctrl+C to stop.")
    try:
        # Simulation Loop
        for _ in range(10): # Run for a few ticks
            time.sleep(1) # 1 sec ticks instead of 100ms for log readability
            for eng in engines:
                # Mock Price Action: Random walk
                import random
                price_move = random.uniform(-1.0, 1.0) # +/- $1
                # We need to get current price again? Or just mock it
                # fetching live price is slow in loop, usually use websocket.
                # Here we mock:
                current_mock = eng.range_high + (price_move if random.random() > 0.5 else -price_move)
                eng.on_tick(current_mock)
                
    except KeyboardInterrupt:
        print("\n🛑 Manual Interruption.")
        
    print("\n🏁 Session Ended.")

if __name__ == "__main__":
    run_orb_session()
