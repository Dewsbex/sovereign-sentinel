import requests
import json
import os
import yfinance as yf
import pandas as pd
import datetime
import logging
from requests.auth import HTTPBasicAuth

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ORB_Observer")

class ORBObserver:
    def __init__(self, config_file="config/orb_config.json"):
        self.config = self.load_config(config_file)
        self.t212_key = os.getenv('T212_API_KEY')
        self.t212_url = "https://live.trading212.com/api/v0/equity"
        self.tickers = self.config['watchlist']
        self.min_rvol = self.config['filters']['min_rvol']

    def load_config(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def get_t212_metadata(self, ticker):
        """Fetches instrument details (min trade qty, currency) from T212."""
        # Note: T212 uses specific codes like "AAPL_US_EQ"
        # We need to find the correct ID map.
        # For efficiency in this "Observer" phase, we just assume standard US_EQ suffix for now
        # But a robust implementation would search the mapping.
        
        # ACTUALLY: Let's fetch ALL instruments once and cache it (optimization).
        # OR: Just fetch specific one if needed.
        
        # V1 Implementation: Just construct the code and verify it exists
        instrument_code = f"{ticker}_US_EQ" 
        url = f"{self.t212_url}/metadata/instruments/{instrument_code}"
        
        try:
            resp = requests.get(url, headers={"Authorization": self.t212_key}) # Metadata valid without key? Usually needs it.
            # Using Requests with Auth
            # Actually, standard practice is requests.get(url, headers=header)
            # Let's use the explicit Auth header format
            headers = {"Authorization": self.t212_key}
            resp = requests.get(url, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.warning(f"Metadata lookup failed for {ticker}: {resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"T212 Connection Error: {e}")
            return None

    def calculate_rvol(self, ticker):
        """Calculates Relative Volume (RVOL) for the 14:30-14:45 candle."""
        logger.info(f"Calculating RVOL for {ticker}...")
        
        try:
            # 1. Fetch 10 days of 15m data
            ticker_obj = yf.Ticker(ticker)
            # Get last 5 days to be safe with limits, interval 15m
            # We want the OPENING candle of each day.
            df = ticker_obj.history(period="5d", interval="15m")
            
            if df.empty:
                logger.warning(f"No data for {ticker}")
                return 0.0

            # 2. Filter for just the opening 15m candles (09:30 - 09:45 NY Time)
            # YFinance returns time in local timezone usually.
            # Let's assume standard index slicing.
            
            # Simple approximation: Take the *first* candle of each unique Date
            df['Date'] = df.index.date
            opening_candles = df.groupby('Date').head(1)
            
            # 3. Calculate Average Volume of these openers
            # Exclude TODAY from the average (we want to compare against today)
            today_date = datetime.datetime.now().date()
            past_openers = opening_candles[opening_candles.index.date < today_date]
            
            if past_openers.empty:
                logger.warning("Not enough history for RVOL average")
                return 1.0 # Default safe

            avg_vol = past_openers['Volume'].mean()
            
            # 4. Get Today's Opening Volume (The most recent incomplete/complete candle depending on time)
            # If running AT 14:26 GMT (09:26 NY), the 09:30 candle doesn't exist yet!
            # WAIT. 
            # The strategy says "Observation Window 14:30 - 14:45 GMT".
            # This implies we are observing LIVE.
            # So we can't get "Today's Volume" from YF history until the candle CLOSES or updates.
            # YFinance has ~15min delay usually.
            
            # CRITICAL ADJUSTMENT: 
            # If running live, YFinance might be delayed.
            # We should use T212 WebSocket or Polling for "Current Vol" if possible?
            # T212 API doesn't give volume easily.
            # YFinance *Real-Time* (period='1d', interval='1m') might give recent ticks?
            
            # HYBRID APPROACH for v32.24:
            # We use YF for the *Average* (Benchmark).
            # We assume we are running this script *after* market open? 
            # Or is this PRE-market prep?
            # 
            # User Spec: "Startup: Initialize WebSocket at 14:25 GMT."
            # "Observation Window (14:30 – 14:45 GMT)"
            # "RVOL Calculation: Calculate Time-Weighted RVOL (Today's 15m Vol...)"
            
            # If we run this AT 14:45 (End of window), YF might have the data.
            # If we run at 14:25, we have NO volume yet.
            
            # LOGIC FIX:
            # This class calculates the BENCHMARK (Avg 15m Vol) at startup (14:25).
            # During the window (14:30-14:45), the "Execution Engine" counts live ticks/volume (if available)
            # OR we poll YF at 14:45 to decide?
            
            # Let's return the BENCHMARK VOLUME from this function.
            # The "Execution" loop will track accumulated volume or we check snapshot at 14:45.
            
            return avg_vol

        except Exception as e:
            logger.error(f"RVOL Calc Failed for {ticker}: {e}")
            return 0.0

    def calculate_vwap(self, ticker):
        """Calculates Intraday VWAP (Volume Weighted Average Price)."""
        try:
            # Get Intraday Data (1 Minute Intervals, Today)
            df = yf.Ticker(ticker).history(period="1d", interval="1m")
            if df.empty: return 0.0
            
            # VWAP Formula: CumSum(Price * Volume) / CumSum(Volume)
            # Price is typical price: (High + Low + Close) / 3
            df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['PV'] = df['Typical_Price'] * df['Volume']
            
            vwap = df['PV'].cumsum().iloc[-1] / df['Volume'].cumsum().iloc[-1]
            vwap = round(float(vwap), 2)
            logger.info(f"VWAP for {ticker}: {vwap}")
            return vwap
        except Exception as e:
            logger.error(f"VWAP Calc Failed for {ticker}: {e}")
            return 0.0

    def analyze_market_conditions(self):
        """Main method to filter the watchlist."""
        approved = {}
        for t in self.tickers:
            avg_vol = self.calculate_rvol(t)
            vwap = self.calculate_vwap(t)
            
            # We store the benchmark. 
            # Real-time RVOL check happens in the loop.
            approved[t] = {
                "avg_15m_volume": avg_vol,
                "vwap": vwap
            }
        
        return approved

if __name__ == "__main__":
    # Test Run
    obs = ORBObserver()
    results = obs.analyze_market_conditions()
    print(json.dumps(results, indent=2))
