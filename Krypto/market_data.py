import json
import threading
import time
import websocket
import pandas as pd
from datetime import datetime
import logging
import app_config
from normalizer import DataNormalizer

class KrakenWebSocketData:
    """
    Manages WebSocket connection to Kraken for real-time OHLC data.
    """
    def __init__(self, pairs=app_config.TRADING_PAIRS):
        self.pairs = pairs
        self.ws_url = "wss://ws.kraken.com"
        self.ws = None
        self.data_buffer = {pair: [] for pair in pairs}  # Buffer to store raw OHLC
        self.df_buffer = {pair: pd.DataFrame() for pair in pairs} # DF
        self.logger = logging.getLogger('system_logger')
        self.normalizer = DataNormalizer()
        self.lock = threading.Lock()
        self.running = False

    def on_message(self, ws, message):
        try:
            msg = json.loads(message)
            
            # Heartbeat
            if isinstance(msg, dict) and msg.get("event") == "heartbeat":
                return

            # OHLC Update
            # OHLC Update
            if isinstance(msg, list):
                # Msg format: [channelID, [time, etime, open, high, low, close, vwap, vol, count], channelName, pair]
                if len(msg) >= 4 and "ohlc" in str(msg[2]):
                    data = msg[1]
                    ws_pair = msg[3]
                    
                    # Map WS Pair to Config Pair
                    ws_map = {
                        "XBT/GBP": "XXBTZGBP",
                        "ETH/GBP": "XETHZGBP",
                        "SOL/GBP": "SOLGBP"
                    }
                    
                    config_pair = ws_map.get(ws_pair, ws_pair)
                    
                    if config_pair in self.data_buffer:
                        self.process_ohlc_update(config_pair, data)
                    else:
                        self.logger.warning(f"Received data for unconfigured pair: {ws_pair}")

        except Exception as e:
            self.logger.error(f"WS Message Error: {e}")

    def process_ohlc_update(self, pair, data):
        """
        Updates the local DataFrame with new candle data.
        Data: [time, etime, open, high, low, close, vwap, volume, count]
        """
        # Close is index 5
        # We need to build a proper candle row
        timestamp = float(data[1]) # End time
        open_p = float(data[2])
        high_p = float(data[3])
        low_p = float(data[4])
        close_p = float(data[5])
        volume = float(data[7])

        # Normalize logic (Pence Bug Guard)
        # Note: We don't know the exact symbol format from WS here easily without mapping
        # so we pass the pair string.
        close_p = self.normalizer.normalize_price(close_p, pair, "kraken")
        high_p = self.normalizer.normalize_price(high_p, pair, "kraken")
        low_p = self.normalizer.normalize_price(low_p, pair, "kraken")
        open_p = self.normalizer.normalize_price(open_p, pair, "kraken")

        row = {
            'timestamp': datetime.fromtimestamp(timestamp),
            'open': open_p,
            'high': high_p,
            'low': low_p,
            'close': close_p,
            'volume': volume
        }

        with self.lock:
            buffer_list = self.data_buffer[pair]
            
            # Prevent duplicate 5m candles by timestamp comparison
            if buffer_list and buffer_list[-1]['timestamp'] == row['timestamp']:
                buffer_list[-1] = row # Update latest candle
            else:
                buffer_list.append(row) # Append new candle
            
            # Keep buffer size manageable (example: 2000 candles)
            if len(self.data_buffer[pair]) > 2000:
                self.data_buffer[pair].pop(0)

    def get_dataframe(self, pair):
        """Returns a Pandas DataFrame of the pair's data."""
        with self.lock:
            # Check if we have data
            # Map Config pair to WS pair if needed.
            # Config: XXBTZGBP -> WS: XBT/GBP. 
            # Simple heuristic mapping:
            target_key = pair
            if pair == "XXBTZGBP": target_key = "XBT/GBP"
            if pair == "XETHZGBP": target_key = "ETH/GBP"
            # SOLGBP might be SOL/GBP
            
            # Fallback search
            if target_key not in self.data_buffer:
                # Try finding it
                for k in self.data_buffer.keys():
                    if pair in k or k in pair: 
                        target_key = k
                        break
            
            data = self.data_buffer.get(target_key, [])
            if not data:
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            return df

    def on_error(self, ws, error):
        self.logger.error(f"WS Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.logger.warning("WS Closed")

    def on_open(self, ws):
        self.logger.info("WS Opened")
        # Subscribe
        # Map config pairs to WS pairs
        ws_pairs = []
        for p in self.pairs:
            if p == "XXBTZGBP": ws_pairs.append("XBT/GBP")
            elif p == "XETHZGBP": ws_pairs.append("ETH/GBP")
            elif p == "SOLGBP": ws_pairs.append("SOL/GBP")
            else: ws_pairs.append(p)

        sub_msg = {
            "event": "subscribe",
            "pair": ws_pairs,
            "subscription": {
                "name": "ohlc",
                "interval": 5 # 5 minute candles as per strategy
            }
        }
        ws.send(json.dumps(sub_msg))
        self.logger.info(f"Subscribed to {ws_pairs}")

    def start(self):
        self.running = True
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.daemon = True
        self.thread.start()

if __name__ == "__main__":
    # Test
    kws = KrakenWebSocketData()
    kws.start()
    try:
        while True:
            time.sleep(10)
            df = kws.get_dataframe("XXBTZGBP")
            if not df.empty:
                print(f"Latest Data for XBT:\n{df.tail(2)}")
            else:
                print("Waiting for data...")
    except KeyboardInterrupt:
        print("Stopping...")
