"""
Sovereign Architect v31.0 Gold Master
The Central Intelligence for Sovereign Sentinel.
Includes SniperScope for YFinance Integration.
"""

import pandas as pd
import json
import os
from enum import Enum
from typing import Dict, List, Optional, Tuple
import yfinance as yf
from config import (
    RISK_FREE_RATE, UK_FRICTION, US_FRICTION,
    PENNY_STOCK_THRESHOLD
)

# Math Anchors for v31.0
UK_STAMP_DUTY_FACTOR = 1.005
US_FX_FEE_FACTOR = 1.0015

class BionicTier(Enum):
    """AI/Automation capability tiers"""
    TIER_1_PLUS = "1+"  # Cyborg: Proven AI efficiency
    TIER_1 = "1"        # Sleeper: Structural AI fit
    TIER_2 = "2"        # Classic: Standard value

class SniperScope:
    """
    The External Radar (YFinance).
    Fetches Watchlist prices and FX Rates.
    """
    
    def __init__(self, watchlist_data: Optional[List[Dict]] = None):
        self.watchlist_data = watchlist_data
        self.watchlist_path = 'watchlist.json'
        
    def _t212_to_yahoo(self, ticker: str) -> str:
        """Converts T212 ticker format to Yahoo Finance format."""
        if ticker.endswith('.L'): return ticker # Already good
        if '_UK_' in ticker: return ticker.split('_')[0] + '.L'
        if '_US_' in ticker: return ticker.split('_')[0]
        if 'l_EQ' in ticker: return ticker.replace('l_EQ', '.L')
        return ticker.split('_')[0] # Default fallback

    def scan_targets(self) -> Tuple[pd.DataFrame, float]:
        """
        Alias for fetch_intelligence for v31.1 compliance.
        Returns: (Targets DataFrame, FX Rate float)
        """
        df, rates = self.fetch_intelligence()
        return df, rates.get('GBPUSD', 1.25)

    def fetch_intelligence(self) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """
        Fetches live data for Watchlist + FX Rates.
        Returns: (Targets DataFrame, FX Dict)
        """
        # 1. Load Watchlist
        targets = []
        yahoo_tickers = []
        
        raw_list = []
        if self.watchlist_data:
            raw_list = self.watchlist_data
        else:
            try:
                with open(self.watchlist_path, 'r') as f:
                    raw_list = json.load(f)
            except:
                pass
                
        for item in raw_list:
            t212_ticker = item.get('ticker')
            y_ticker = self._t212_to_yahoo(t212_ticker)
            
            # Preserve all existing fields and add internal ones
            target_data = item.copy()
            target_data.update({
                't212_ticker': t212_ticker,
                'yahoo_ticker': y_ticker,
                'target_price': item.get('target_price', item.get('target', 0)),
                'tier': item.get('tier', '2'),
                'expected_growth': item.get('expected_growth', 0),
                'name': item.get('name', t212_ticker)
            })
            targets.append(target_data)
            yahoo_tickers.append(y_ticker)

        # 2. Add FX Pairs to fetch list
        fx_pair = "GBPUSD=X"
        yahoo_tickers.append(fx_pair)
        
        # 3. Batch Fetch from YFinance
        print(f"[SCOPE] Fetching {len(yahoo_tickers)} assets via YFinance...")
        data = yf.download(yahoo_tickers, period="1d", timeout=5, progress=False)['Close']
        
        # 4. Process FX
        fx_rates = {'GBPUSD': 1.25} # Fallback
        try:
            if not data.empty and fx_pair in data.columns:
                rate = float(data[fx_pair].iloc[-1])
                fx_rates['GBPUSD'] = rate
                print(f"[SCOPE] FX Locked: GBP/USD = {rate:.4f}")
        except Exception as e:
            print(f"[SCOPE] FX Fetch Warning: {e}")

        # 5. Enrich Targets
        processed_targets = []
        for t in targets:
            y_sym = t['yahoo_ticker']
            live_price = 0.0
            
            try:
                # Handle single ticker result vs multi-index
                if len(yahoo_tickers) == 1:
                     # If only 1 ticker (+FX maybe failed?), data series
                     live_price = float(data.iloc[-1])
                elif y_sym in data.columns:
                    live_price = float(data[y_sym].iloc[-1])
            except:
                pass
            
            t['live_price'] = live_price
            
            # Distance Calc
            if t['target_price'] > 0 and live_price > 0:
                t['distance_pct'] = ((live_price - t['target_price']) / t['target_price']) * 100
                t['status'] = "BUY NOW" if live_price <= t['target_price'] else "WATCH"
            else:
                t['distance_pct'] = 0.0
                t['status'] = "UNKNOWN"
            
            processed_targets.append(t)
            
        return pd.DataFrame(processed_targets), fx_rates

class SovereignArchitect:
    """
    The Logic Core.
    Calculates Tiers, Actions, and FX Impact.
    """
    
    def __init__(self, fx_rate: float = 1.25):
        self.fx_rate = fx_rate
        self.bionic_tiers = self._load_bionic_tiers()

    def _load_bionic_tiers(self) -> Dict:
        """Load Bionic Tier classifications or defaults"""
        try:
            with open('bionic_tiers.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def get_limit_price(self, target_price: float, currency: str) -> float:
        """
        Calculates the Safe Buy Limit price including friction.
        v27.0 Math Anchors.
        """
        if currency == 'GBP' or currency == 'GBX':
            # UK Stamp Duty 0.5%
            return target_price / UK_STAMP_DUTY_FACTOR
        elif currency == 'USD':
            # US FX Fee 0.15%
            return target_price / US_FX_FEE_FACTOR
        else:
            return target_price # No friction assumption

    def calculate_fx_impact_v31(self, real_pl_gbp: float, raw_pl_local: float, 
                          current_fx_rate: float, is_usd: bool) -> float:
        """Original v31.0 Logic"""
        if not is_usd: 
            return 0.0
        if current_fx_rate == 0: 
            return 0.0
        natural_pl_gbp = raw_pl_local / current_fx_rate
        return real_pl_gbp - natural_pl_gbp

    def calculate_fx_impact(self, pl, price, avg, shares, is_us):
        """v31.1 Specific Logic"""
        if not is_us: return 0.0
        # Formula: (Real_PL_GBP) - ((Live_Price - Avg_Price) * Shares * Fixed_FX_Rate)
        # Simplified: pl (GBP) - ((price - avg) * shares / fx_rate)
        theoretical_pl_gbp = ((price - avg) * shares) / self.fx_rate
        return pl - theoretical_pl_gbp

    def get_tier(self, ticker: str) -> str:
        """Alias for classify_tier"""
        return self.classify_tier(ticker)

    def classify_tier(self, ticker: str) -> str:
        """Determines Bionic Tier string"""
        # Simplify: Check JSON or logic
        # For now return "2" or lookup
        # ... logic ...
        return "2" # Default

if __name__ == "__main__":
    # Test
    print("Testing SniperScope...")
    scope = SniperScope()
    df, rates = scope.fetch_intelligence()
    print("FX Rates:", rates)
    print("Targets Head:")
    print(df.head())
