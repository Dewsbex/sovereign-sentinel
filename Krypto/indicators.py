import pandas as pd
import numpy as np

class TechnicalIndicators:
    """
    Manual implementation of technical indicators using Pandas/Numpy.
    Removes dependency on heavy libraries like TA-Lib or Pandas-TA for stability.
    """

    @staticmethod
    def calculate_ema(df, period=20, column='close'):
        """Calculates Exponential Moving Average."""
        return df[column].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(df, period=14, column='close'):
        """Calculates Relative Strength Index."""
        delta = df[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Wilder's Smoothing for better accuracy like TradingView
        # (Recursive implementation is harder to vectorize, so simple rolling is used for speed)
        # Ideally, we should use ewm for Wilder's but rolling is acceptable for retail bots.
        return rsi

    @staticmethod
    def calculate_atr(df, period=14):
        """Calculates Average True Range."""
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def calculate_vwap(df):
        """
        Calculates Volume Weighted Average Price.
        If data is intra-day, this should be reset daily. 
        Assuming incoming DF is the relevant session data.
        """
        v = df['volume']
        tp = (df['high'] + df['low'] + df['close']) / 3
        return (tp * v).cumsum() / v.cumsum()

    @staticmethod
    def add_all_indicators(df):
        """Applies all standard strategy indicators to the DataFrame."""
        df['ema_20'] = TechnicalIndicators.calculate_ema(df, 20)
        df['ema_50'] = TechnicalIndicators.calculate_ema(df, 50)
        df['rsi'] = TechnicalIndicators.calculate_rsi(df, 14)
        df['atr'] = TechnicalIndicators.calculate_atr(df, 14)
        df['vwap'] = TechnicalIndicators.calculate_vwap(df)
        return df
