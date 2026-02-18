import json
import os
from datetime import datetime

class SessionManager:
    """
    Manages the Session Whitelist to isolate Day Trading from Long Term Holdings.
    Only tickers added to this whitelist (bought during the session) are eligible for:
    1. Curfew Liquidation
    2. Stop Loss / Take Profit checks (redundant safety)
    """
    def __init__(self, filepath='data/session_whitelist.json'):
        self.filepath = filepath
        self.whitelist = self._load_whitelist()

    def _load_whitelist(self):
        """Loads whitelist, resetting it if the date has changed (New Session)"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        
        if not os.path.exists(self.filepath):
            return {"date": datetime.utcnow().strftime('%Y-%m-%d'), "tickers": []}
        
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                
            # Date Check - Reset if old
            today = datetime.utcnow().strftime('%Y-%m-%d')
            if data.get('date') != today:
                return {"date": today, "tickers": []}
                
            return data
        except Exception as e:
            print(f"⚠️ Whitelist Load Error: {e}. Resetting.")
            return {"date": datetime.utcnow().strftime('%Y-%m-%d'), "tickers": []}

    def _save_whitelist(self):
        """Persists whitelist to disk"""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            json.dump(self.whitelist, f, indent=2)

    def add_ticker(self, ticker):
        """Adds a ticker to the session whitelist (on Buy)"""
        # Normalize ticker? T212 might have _US_EQ.
        # usually logic uses raw ticker.
        if ticker not in self.whitelist['tickers']:
            self.whitelist['tickers'].append(ticker)
            self._save_whitelist()
            print(f"🛡️ SESSION MANAGER: {ticker} added to whitelist.")

    def is_whitelisted(self, ticker):
        """Checks if ticker is in the current session whitelist"""
        # Auto-reset if day changed mid-run
        today = datetime.utcnow().strftime('%Y-%m-%d')
        if self.whitelist.get('date') != today:
            self.whitelist = {"date": today, "tickers": []}
            self._save_whitelist()
            return False
            
        return ticker in self.whitelist['tickers']

    def get_whitelist(self):
        return self.whitelist['tickers']
