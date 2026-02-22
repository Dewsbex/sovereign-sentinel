"""
VWAP Pullback Strategy — Institutional Mean-Reversion for Krypto.
After a strong morning trend is established, buy when price pulls back to touch VWAP.
This is where institutions reload positions — the "gravitational centre" of liquidity.
"""
import pandas as pd
import math
import logging
from datetime import datetime
from indicators import TechnicalIndicators
import app_config

class VWAPPullbackStrategy:
    def __init__(self):
        self.logger = logging.getLogger('trade_logger')
        self.trend_bias = None  # 'BULLISH' or 'BEARISH' — set by ORB result
        self.active = False
    
    def set_trend_bias(self, bias: str):
        """
        Called after ORB session establishes direction.
        If ORB triggered a BUY → trend_bias = BULLISH (look for VWAP pullback longs).
        """
        self.trend_bias = bias
        self.active = True
        self.logger.info(f"VWAP PULLBACK: Trend bias set to {bias}")
    
    def reset_daily_state(self):
        self.trend_bias = None
        self.active = False
        self.logger.info("VWAP PULLBACK: Reset for new day")
    
    def execute_logic(self, df_5m: pd.DataFrame) -> dict:
        """
        Check for VWAP pullback entry on each 5-min candle close.
        
        Entry Conditions (BULLISH):
        1. ORB session established bullish bias
        2. Price was trending above VWAP (at least 3 of last 5 candles above VWAP)
        3. Current candle touches or dips below VWAP (low <= VWAP)
        4. Current candle closes above VWAP (buyers defending)
        5. RSI between 40-60 (not overbought/oversold — healthy pullback)
        """
        if not self.active or not self.trend_bias:
            return None
        
        if df_5m.empty or len(df_5m) < 20:
            return None
        
        # Only do bullish pullbacks for now (bearish is the inverse)
        if self.trend_bias != "BULLISH":
            return None
        
        # Enrich with indicators
        df_indic = TechnicalIndicators.add_all_indicators(df_5m.copy())
        if df_indic.empty:
            return None
        
        current = df_indic.iloc[-1]
        vwap = current.get('vwap', float('nan'))
        rsi = current.get('rsi', float('nan'))
        atr = current.get('atr', float('nan'))
        
        if math.isnan(vwap) or math.isnan(rsi) or math.isnan(atr):
            return None
        
        # Condition 1: Price was trending above VWAP (3 of last 5 candles)
        recent = df_indic.tail(5)
        above_vwap_count = sum(1 for _, r in recent.iterrows() 
                               if not math.isnan(r.get('vwap', float('nan'))) 
                               and r['close'] > r['vwap'])
        
        if above_vwap_count < 3:
            return None  # No clear uptrend relative to VWAP
        
        # Condition 2: Current candle touches VWAP (low touches or dips below)
        if current['low'] > vwap:
            return None  # Price hasn't pulled back to VWAP yet
        
        # Condition 3: Current candle closes ABOVE VWAP (buyers defending)
        if current['close'] <= vwap:
            return None  # Close below VWAP = VWAP lost, trend may be failing
        
        # Condition 4: RSI in healthy pullback zone (not extreme)
        if rsi < 40 or rsi > 65:
            return None  # Too weak or too extended
        
        # SIGNAL CONFIRMED — VWAP Pullback Long
        entry_price = current['close']
        stop_loss = current['low'] - (atr * 0.5)  # Below the pullback low + buffer
        risk = entry_price - stop_loss
        take_profit = entry_price + (risk * 1.5)  # 1.5R target
        
        signal = {
            "type": "BUY",
            "strategy": "VWAP_PULLBACK",
            "price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "take_profit_r": 1.5,
            "timestamp": datetime.utcnow(),
            "vwap": vwap,
            "rsi": rsi
        }
        
        self.logger.info(f"VWAP PULLBACK SIGNAL: Entry={entry_price:.2f}, SL={stop_loss:.2f}, "
                        f"TP={take_profit:.2f}, VWAP={vwap:.2f}, RSI={rsi:.1f}")
        
        # Deactivate after first signal to prevent multiple entries on same pullback
        self.active = False
        
        return signal


if __name__ == "__main__":
    print("=== VWAP Pullback Strategy ===")
    strategy = VWAPPullbackStrategy()
    strategy.set_trend_bias("BULLISH")
    print(f"Active: {strategy.active}, Bias: {strategy.trend_bias}")
