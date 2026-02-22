import pandas as pd
import numpy as np

class SmartMoneyConcepts:
    """
    Implements institutional order flow concepts:
    - Displacement (Big energetic moves)
    - Fair Value Gaps (FVG) / Imbalances
    """

    @staticmethod
    def is_displacement_candle(df, index=-1, magnitude_factor=2.0):
        """
        Checks if the candle at 'index' is a displacement candle.
        Displacement = Body size is > X times the average body size of recent history.
        """
        if len(df) < 21:
            return False

        current_candle = df.iloc[index]
        body_size = abs(current_candle['close'] - current_candle['open'])
        
        # Calculate recent average body size (last 20 candles)
        # Using abs() to get magnitude of bodies
        recent_bodies = (df['close'] - df['open']).abs().rolling(20).mean()
        avg_body = recent_bodies.iloc[index]

        return body_size > (avg_body * magnitude_factor)

    @staticmethod
    def detect_fvg(df, index=-1):
        """
        Checks for a Fair Value Gap (Imbalance) formed by the validation sequence.
        Standard Bullish FVG:
        Candle A (index-2)
        Candle B (index-1) - The Breakout Impulse
        Candle C (index) - The confirmation/current
        
        A Bullish FVG exists if there is a gap between Candle A's High and Candle C's Low.
        Low[index] > High[index-2]
        """
        if len(df) < 3:
            return False

        candle_c = df.iloc[index]      # Current/Confirmation
        candle_a = df.iloc[index-2]    # Pre-impulse

        # Bullish Imbalance
        # The low of the 3rd candle must be higher than the high of the 1st candle
        if candle_c['low'] > candle_a['high']:
            return True, "BULLISH", candle_a['high'], candle_c['low']
        
        # Bearish Imbalance
        # The high of the 3rd candle must be lower than the low of the 1st candle
        if candle_c['high'] < candle_a['low']:
            return True, "BEARISH", candle_c['high'], candle_a['low']

        return False, "NONE", 0, 0
