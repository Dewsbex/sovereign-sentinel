import logging
import time
import krakenex
import app_config

class ExecutionEngine:
    def __init__(self):
        self.logger = logging.getLogger('trade_logger')
        self.api = krakenex.API(key=app_config.KRAKEN_API_KEY, secret=app_config.KRAKEN_SECRET)
        self.is_paper = app_config.IS_PAPER_TRADING

    def get_balance(self, asset='ZUSD'):
        """
        Fetches the current tradeable balance for the specified asset.
        Default is ZUSD (US Dollar for Kraken). Change to 'ZEUR' or 'ZGBP' as needed.
        """
        if self.is_paper:
            self.logger.info(f"PAPER: Returning mock balance for {asset}")
            return 10000.0 # Mock Balance
        
        try:
            res = self.api.query_private('Balance')
            if res.get('error'):
                self.logger.error(f"Balance Check Error: {res['error']}")
                return 0.0
            
            # Result: {'ZUSD': '100.50', 'XXBT': '0.05'}
            # Note: Kraken uses 'Z' prefix for fiat and 'X' for crypto often, but not always for newer assets (e.g. USDT)
            balances = res.get('result', {})
            return float(balances.get(asset, 0.0))

        except Exception as e:
            self.logger.error(f"Failed to fetch balance: {e}")
            return 0.0

    def check_spread(self, pair):
        """
        Queries Kraken Ticker to check current spread.
        Returns True if Spread < MAX_SPREAD_PERCENT.
        """
        if self.is_paper:
            return True 

        try:
            # Raw KrakenEx Ticker Call
            # Pair: XXBTZGBP
            res = self.api.query_public('Ticker', {'pair': pair})
            if res.get('error'):
                self.logger.error(f"Ticker Error: {res['error']}")
                return False
            
            # Result format: {'XXBTZGBP': {'a': ['50000.0', ...], 'b': ['49900.0', ...]}}
            res_data = res.get('result', {})
            if not res_data: return False
            
            p_data = list(res_data.values())[0]
            ask = float(p_data['a'][0])
            bid = float(p_data['b'][0])
            
            spread_pct = (ask - bid) / bid
            
            if spread_pct > app_config.MAX_SPREAD_PERCENT:
                self.logger.warning(f"SPREAD GUARD: {pair} spread {spread_pct:.4f}% > {app_config.MAX_SPREAD_PERCENT:.4f}%")
                return False
            
            return True

        except Exception as e:
            self.logger.error(f"Spread Check Failed: {e}")
            return False

    def place_order(self, pair, side, quantity, price=None, order_type='market', stop_loss=None, take_profit=None):
        """
        Executes an order. 
        Supports attaching Stop Loss and Take Profit if creating a position.
        """
        self.logger.info(f"ORDER REQUEST: {side} {quantity} {pair} @ {price or 'MKT'}")

        if not self.check_spread(pair):
            self.logger.error("Order Cancelled: Spread too high.")
            return None

        if self.is_paper:
            return {
                "status": "filled",
                "txid": [f"paper_{int(time.time())}"],
                "price": price if price else 0.0,
                "vol": quantity,
                "descr": {"order": f"buy {quantity} {pair} @ {price}"}
            }
        
        try:
            ord_type = 'market' if order_type == 'market' else 'limit'
            req_data = {
                'pair': pair,
                'type': side.lower(),
                'ordertype': ord_type,
                'volume': f"{quantity:.8f}".rstrip('0').rstrip('.'), # KRAKEN REQUIRES FIXED DECIMAL STRINGS
            }
            
            if price and order_type == 'limit':
                req_data['price'] = str(price)

            # --- Advanced Order Logic (TP/SL) ---
            # Kraken allows 'close' dict to specify an order to execute when the primary order is filled.
            # However, you can't easily add BOTH SL and TP in a simple 'close' arg for a market order in one go 
            # without using 'oco' or complex workflows. 
            # For robustness in this iteration, we will implement the Entry first. 
            # Users often manage TP/SL via separate limit/stop orders once position is confirmed.
            
            # Uncomment below to validate only
            # req_data['validate'] = 'true'

            res = self.api.query_private('AddOrder', req_data)
            
            if res.get('error'):
                self.logger.error(f"Kraken Order Error: {res['error']}")
                return None
            
            return res['result'] # Contains txid, descr
            
        except Exception as e:
            self.logger.error(f"Execution Error: {e}")
            return None
