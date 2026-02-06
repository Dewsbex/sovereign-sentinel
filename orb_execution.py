import time
import datetime
import requests
import json
import logging
import os
from requests.auth import HTTPBasicAuth

# Logger
logger = logging.getLogger("ORB_Execution")

class ORBExecutionEngine:
    def __init__(self, state_manager, messenger, config_file="config/orb_config.json"):
        self.state_manager = state_manager
        self.messenger = messenger
        with open(config_file, 'r') as f:
            self.config = json.load(f)
            
        self.t212_key = os.getenv('T212_API_KEY')
        self.t212_secret = os.getenv('T212_API_SECRET') # Needed for Place Order
        self.auth = HTTPBasicAuth(self.t212_key, self.t212_secret)
        self.base_url = "https://live.trading212.com/api/v0/equity"
        
        # Runtime State
        self.ranges = {} # {ticker: {high: x, low: y, active: True/False}}

    def fetch_current_price(self, ticker):
        """Fetches the latest price snapshot (Simulating WebSocket ticking)."""
        # In a real WebSocket impl, this would return the cached latest tick.
        # For this REST-based polling implementation:
        # We can use /equity/pricing or just get the instrument details? 
        # T212 API v0 doesn't have a simple "Quote" endpoint for bulk.
        # We have to iterate or use a simpler proxy?
        # OPTIMIZATION: We skip this implementation detail for the skeletal build
        # and assume we have a way to get price (e.g. from YFinance live or T212 workaround).
        
        # PROXY: Use Requests to a public source or T212 if endpoint exists.
        # Let's assume (for now) we are running this in a loop that *somehow* gets data.
        # To make this runnable, we will use a placeholder that returns a dummy or YF price.
        return 0.0

    def set_range(self, ticker, high, low, vwap=0.0):
        """Sets the 15-minute Opening Range for a ticker."""
        r_pct = (high - low) / low * 100
        min_r = self.config['risk']['min_range_percent']
        
        if r_pct < min_r:
            logger.info(f"🚫 Range too tight for {ticker} ({r_pct:.2f}% < {min_r}%). Skipping.")
            self.ranges[ticker] = {"active": False}
        else:
            logger.info(f"✅ Range SET for {ticker}: {low} - {high} ({r_pct:.2f}%) [VWAP: {vwap}]")
            self.ranges[ticker] = {
                "high": high, 
                "low": low, 
                "vwap": vwap,
                "active": True,
                "trigger_long": high + 0.01,
                "trigger_short": low - 0.01,
                "bracket": { # Bracket Simulation
                    "stop_loss": low,
                    "take_profit_2r": high + (2 * (high - low))
                }
            }

    def place_order(self, ticker, side, quantity, price=None):
        """Executes the trade via T212 API."""
        # Convert side to API format (Official Spec v0)
        # Buy = Positive Quantity
        # Sell = Negative Quantity
        # Key = 'ticker', NOT 'instrumentCode'
        
        signed_qty = quantity if side == "BUY" else -quantity
        
        payload = {
            "ticker": f"{ticker}_US_EQ", # Spec says key is 'ticker', value example 'AAPL_US_EQ'
            "quantity": signed_qty,
            "timeValidity": "DAY"
        }
        
        if price:
            payload["limitPrice"] = price
            # Endpoint: /orders/limit
            endpoint = "/orders/limit"
        else:
            # Endpoint: /orders/market
            endpoint = "/orders/market"
        
        logger.info(f"🚀 SENDING ORDER: {side} {quantity} {ticker} (Signed: {signed_qty})...")
        try:
            resp = requests.post(f"{self.base_url}{endpoint}", json=payload, auth=self.auth, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"✅ ORDER FILLED/PLACED: ID {data.get('id')}")
                
                # Slippage Audit
                fill_price = float(data.get('averagePrice', 0) or data.get('price', price or 0)) # Assuming API returns avgPrice
                expected = price if price else 0 # If market, hard to know Expected without ticker price arg
                
                if fill_price > 0 and expected > 0:
                    slip_pct = abs(fill_price - expected) / expected
                    if slip_pct > 0.002: # 0.2% Limit
                        logger.warning(f"⚠️ SLIPPAGE ALERT: {slip_pct*100:.3f}% > 0.2%. INITIATING EMERGENCY EXIT.")
                        self.messenger.notify_error("Execution", f"Slippage > 0.2% on {ticker}. Closing.")
                        self.place_order(ticker, "SELL", quantity) # Close immediately
                        return None
                
                self.messenger.notify_trade(ticker, side, quantity, fill_price)
                return data
            else:
                logger.error(f"❌ ORDER FAILED: {resp.text}")
                return None
        except Exception as e:
            logger.error(f"Order Connection Error: {e}")
            return None

    def execute_logic_cycle(self, ticker, current_price, is_candle_close=False):
        """The main 'Tick' logic. Called every loop."""
        r = self.ranges.get(ticker)
        if not r or not r['active']:
            return

        # 1. VWAP Guard (Trend Bias)
        vwap = r.get('vwap', 0)
        long_bias = current_price > vwap if vwap > 0 else True
        
        # 2. Candle Close Confirmation (v32.60)
        # Spec: "Fire place_market_order() only if candle_close > range_high"
        # Since we don't have a live websocket here, we rely on the `is_candle_close` flag passed from main loop.
        if not is_candle_close:
            return 

        # Check Long Breakout (Close > High)
        if current_price > r['high'] and long_bias:
             logger.info(f"🟢 5m CANDLE CLOSE BREAKOUT (Bias: {long_bias}): {ticker} @ {current_price} > {r['high']}")
             
             qty = self.calculate_position_size(ticker, current_price)
             if qty > 0:
                 # Market Order for Speed
                 order = self.place_order(ticker, "BUY", qty, price=current_price) 
                 if order:
                     self.ranges[ticker]['active'] = False
                     self.messenger.notify_shield(ticker, r['bracket']['stop_loss'], r['bracket']['take_profit_2r'])
                     return {"action": "FILLED", "order_id": order.get('id'), "side": "BUY", "price": current_price}

        # Check Short Breakout (Inverse logic if needed, spec says ISA Long Only so maybe skip?)
        # Spec 6: "ISA Compliance: Only Long positions." -> Bearish needs Inverse ETP.
        # We will keep it simple: Only Long Breakouts for now unless mapped.
        
        return None

    def calculate_position_size(self, ticker, price):
        budget = self.state_manager.get_allocation_amount()
        if budget <= 0: return 0
        
        qty = budget / price
        # Truncate to sensible decimal (e.g. 2 places or use Metadata minStep)
        # For safety, round down to 1 decimal or integer depending on asset
        return round(qty, 1) 
