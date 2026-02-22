import pandas as pd
from datetime import datetime
import logging
import time
from indicators import TechnicalIndicators
from smart_money import SmartMoneyConcepts
import app_config
import math

class ORBStrategy:
    """
    Augmented Opening Range Breakout — supports multiple sessions.
    Each session (London/NY) gets its own independent range and execution window.
    """
    def __init__(self, session_name="NY"):
        self.logger = logging.getLogger('trade_logger')
        self.session_name = session_name
        self.range_high = None
        self.range_low = None
        self.range_formed = False
        self.signal_fired = False  # Prevent multiple signals per session
    
    def reset_daily_state(self):
        self.range_high = None
        self.range_low = None
        self.range_formed = False
        self.signal_fired = False
        self.logger.info(f"STRATEGY RESET [{self.session_name}]: New Trading Day")

    def set_range(self, high, low):
        self.range_high = high
        self.range_low = low
        self.range_formed = True
        self.logger.info(f"ORB RANGE SET [{self.session_name}]: High={self.range_high}, Low={self.range_low}")

    def execute_logic(self, df_5m):
        """
        Main Loop logic called every time a 5-min candle closes.
        """
        if df_5m.empty or not self.range_formed or self.signal_fired:
            return None

        # Check Breakout Signal
        # Most recent closed candle
        last_candle = df_5m.iloc[-1]
        
        # Enrich with Indicators
        df_indic = TechnicalIndicators.add_all_indicators(df_5m.copy())
        if df_indic.empty:
            return None
        current_indic = df_indic.iloc[-1]
        
        signal = None
        
        # BULLISH BREAKOUT
        # Check if closing price > Range High
        if last_candle['close'] > self.range_high:
            self.logger.info(f"[{self.session_name}] POTENTIAL BREAKOUT: Close {last_candle['close']} > Range High {self.range_high}")
            
            # --- GATES ---
            
            # Gate A: VWAP
            if app_config.VWAP_GATE_ENABLED:
                vwap_val = current_indic['vwap']
                if not math.isnan(vwap_val) and last_candle['close'] < vwap_val:
                    self.logger.info(f"[{self.session_name}] GATE BLOCKED: Price < VWAP ({vwap_val:.2f})")
                    return None
            
            # Gate B: ATR
            if app_config.ATR_GUARD_ENABLED:
                atr_current = current_indic['atr']
                if not math.isnan(atr_current):
                    # Compare with rolling mean
                    atr_mean = df_indic['atr'].rolling(20).mean().iloc[-1]
                    if not math.isnan(atr_mean) and atr_current < (atr_mean * 1.0):
                         self.logger.info(f"[{self.session_name}] GATE BLOCKED: Low Volatility (ATR {atr_current:.2f} < Avg {atr_mean:.2f})")
                         return None

            # Gate C: RSI Momentum
            if app_config.RSI_GATE_ENABLED:
                rsi_val = current_indic['rsi']
                if not math.isnan(rsi_val) and rsi_val < 50:
                    self.logger.info(f"[{self.session_name}] GATE BLOCKED: RSI Weak ({rsi_val:.2f})")
                    return None
            
            # Gate D: Smart Money (Displacement + FVG)
            if app_config.FVG_FILTER_ENABLED:
                # Check if breakout candle shows institutional displacement
                if not SmartMoneyConcepts.is_displacement_candle(df_5m, index=-1, magnitude_factor=2.0):
                    self.logger.info(f"[{self.session_name}] GATE BLOCKED: No Displacement on breakout candle")
                    return None
                
                # Check for Fair Value Gap (proves institutional capital, not retail chasing)
                fvg_result = SmartMoneyConcepts.detect_fvg(df_5m, index=-1)
                has_fvg = fvg_result[0] if isinstance(fvg_result, tuple) else fvg_result
                if not has_fvg:
                    self.logger.info(f"[{self.session_name}] GATE BLOCKED: No FVG present — breakout lacks institutional backing")
                    return None
                
                fvg_direction = fvg_result[1] if isinstance(fvg_result, tuple) else "NONE"
                if fvg_direction != "BULLISH":
                    self.logger.info(f"[{self.session_name}] GATE BLOCKED: FVG direction is {fvg_direction}, not BULLISH")
                    return None
                
                self.logger.info(f"[{self.session_name}] GATE D PASSED: Displacement + Bullish FVG confirmed")
            
            # ALL GATES PASSED
            stop_loss = (self.range_high + self.range_low) / 2
            entry_price = last_candle['close']
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * 1.5)

            signal = {
                "type": "BUY",
                "strategy": f"ORB_{self.session_name}",
                "price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "take_profit_r": 1.5,
                "timestamp": datetime.utcnow()
            }
            self.signal_fired = True
            self.logger.info(f"[{self.session_name}] SIGNAL GENERATED: {signal}")
            return signal
        
        return None

if __name__ == "__main__":
    pass
