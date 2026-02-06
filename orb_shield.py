import requests
import json
import logging
import os
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("ORB_Shield")

class ORBShield:
    def __init__(self, messenger, config_file="config/orb_config.json"):
        self.messenger = messenger
        self.t212_key = os.getenv('T212_API_KEY')
        self.t212_secret = os.getenv('T212_API_SECRET')
        self.auth = HTTPBasicAuth(self.t212_key, self.t212_secret)
        self.base_url = "https://live.trading212.com/api/v0/equity"

    def activate_shield(self, ticker, entry_price, range_high, range_low, qty, side="BUY"):
        """Places Stop Loss and Take Profit orders."""
        logger.info(f"🛡️ ACTIVATING SHIELD for {ticker}...")
        
        # 1. Calculate Levels
        # Range Size
        range_size = range_high - range_low
        
        if side == "BUY":
            stop_price = range_low
            target_price = entry_price + (range_size * 2.0)
        else:
            # Short logic (if we were using CFDs or selling positions)
            # For ISA/Invest, we only SELL what we own.
            pass
            
        logger.info(f"   🛑 STOP: {stop_price:.2f} | 🎯 TARGET: {target_price:.2f}")
        
        ids = {}
        
        # 2. Place STOP LOSS
        # POST /orders/stop
        stop_payload = {
            "instrumentCode": f"{ticker}_US_EQ",
            "quantity": qty, # Sell the same amount
            "side": "SELL", # Closing the Buy
            "stopPrice": stop_price,
            "timeValidity": "DAY" # Or GTC
        }
        try:
            r_stop = requests.post(f"{self.base_url}/orders/stop", json=stop_payload, auth=self.auth)
            if r_stop.status_code == 200:
                ids['stop_id'] = r_stop.json().get('id')
                logger.info(f"   ✅ STOP PLACED: ID {ids['stop_id']}")
            else:
                logger.error(f"   ❌ STOP FAILED: {r_stop.text}")
        except Exception as e:
            logger.error(f"Stop Order Error: {e}")

        # 3. Place TAKE PROFIT (Limit Sell)
        # POST /orders/limit
        limit_payload = {
            "instrumentCode": f"{ticker}_US_EQ",
            "quantity": qty,
            "side": "SELL",
            "limitPrice": target_price,
            "timeValidity": "DAY" # Or GTC
        }
        try:
            r_limit = requests.post(f"{self.base_url}/orders/limit", json=limit_payload, auth=self.auth)
            if r_limit.status_code == 200:
                ids['target_id'] = r_limit.json().get('id')
                logger.info(f"   ✅ TARGET PLACED: ID {ids['target_id']}")
            else:
                logger.error(f"   ❌ TARGET FAILED: {r_limit.text}")
        except Exception as e:
            logger.error(f"Target Order Error: {e}")
            
        self.messenger.notify_shield(ticker, stop_price, target_price)
        return ids

    def check_oco(self, stop_id, target_id):
        """Monitors the bracket. If one fills, cancel the other."""
        # This would be called in the main loop.
        # Check status of Stop
        # Check status of Target
        # If Stop == FILLED -> Cancel Target
        # If Target == FILLED -> Cancel Stop
        pass
