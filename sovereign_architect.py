import pandas as pd
import yfinance as yf
import numpy as np

class SovereignArchitect:
    def __init__(self, fx_rate):
        self.fx_rate = fx_rate

    def generate_sparkline(self, ticker_yf, hist_data):
        try:
            if ticker_yf not in hist_data.columns.levels[0]: return ""
            closes = hist_data[ticker_yf]['Close'].dropna().tolist()
            if len(closes) < 2: return ""
            min_p, max_p = min(closes), max(closes)
            points = []
            w, h = 60, 20
            for i, p in enumerate(closes):
                x = i * (w / (len(closes) - 1))
                y = h - ((p - min_p) / (max_p - min_p) * h) if max_p != min_p else h/2
                points.append(f"{x},{y}")
            color = "#10b981" if closes[-1] >= closes[0] else "#ef4444"
            return f'<svg width="{w}" height="{h}"><polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"/></svg>'
        except: return ""

    def get_tier(self, ticker):
        cyborgs = ['GOOGL', 'AMZN', 'MSFT', 'META', 'NVDA', 'PLTR', 'TSLA']
        return "1+ (Cyborg)" if any(c in ticker for c in cyborgs) else "1 (Sleeper)"
