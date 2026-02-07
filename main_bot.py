"""
Wealth Seeker v0.01 - Main Trading Bot (main_bot.py)
=====================================================
Job C: The Wealth Seeker Sentinel - 5% Autonomous ORB Strategy
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import yfinance as yf
from auditor import TradingAuditor, emergency_shutdown


class AlphaVantageClient:
    """Client for Alpha Vantage API (VWAP and technical data)"""
    
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY not set")
    
    def get_vwap(self, symbol: str) -> Optional[float]:
        """Fetch current VWAP for symbol"""
        try:
            params = {
                "function": "VWAP",
                "symbol": symbol,
                "interval": "5min",
                "apikey": self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract most recent VWAP value
            technical_data = data.get("Technical Analysis: VWAP", {})
            if technical_data:
                latest_timestamp = sorted(technical_data.keys())[-1]
                vwap = float(technical_data[latest_timestamp].get("VWAP", 0))
                return vwap
            
            return None
        except Exception as e:
            print(f"⚠️  Failed to fetch VWAP for {symbol}: {e}")
            return None


class TelegramNotifier:
    """Send notifications via Telegram"""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token or not self.chat_id:
            print("⚠️  Telegram credentials not configured")
    
    def send_message(self, message: str):
        """Send text message to Telegram"""
        if not self.token or not self.chat_id:
            print(f"📱 [Telegram Disabled] {message}")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print(f"✅ Telegram notification sent")
        except Exception as e:
            print(f"⚠️  Telegram send failed: {e}")


class T212Executor:
    """Execute trades via Trading212 API"""
    
    def __init__(self):
        self.api_key = os.getenv("T212_API_TRADE_KEY")
        self.base_url = "https://live.trading212.com/api/v0"
        
        if not self.api_key:
            raise ValueError("T212_API_TRADE_KEY not set")
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
    
    def get_account_info(self) -> Dict[str, Any]:
        """Fetch account summary"""
        url = f"{self.base_url}/equity/account/cash"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    def place_market_order(self, ticker: str, quantity: int) -> Dict[str, Any]:
        """Place market buy order"""
        url = f"{self.base_url}/equity/orders/market"
        payload = {
            "ticker": ticker,
            "quantity": quantity
        }
        response = requests.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        return response.json()


class ORBStrategy:
    """Opening Range Breakout Strategy Implementation"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.market_open = "14:30"  # UTC
        self.orb_duration_minutes = 5
        self.current_high = None
        self.orb_complete = False
    
    def fetch_opening_range(self) -> Optional[float]:
        """Get the high of first 5 minutes (14:30-14:35 UTC)"""
        try:
            # Use yfinance to get 5-minute bars
            stock = yf.Ticker(self.ticker)
            hist = stock.history(period="1d", interval="5m")
            
            if hist.empty:
                print(f"❌ No data for {self.ticker}")
                return None
            
            # Get first 5-min candle of the day
            first_candle = hist.iloc[0]
            self.current_high = first_candle['High']
            
            print(f"📊 {self.ticker} Opening Range High: ${self.current_high:.2f}")
            return self.current_high
            
        except Exception as e:
            print(f"❌ Failed to fetch opening range: {e}")
            return None
    
    def check_breakout(self, current_price: float) -> bool:
        """Check if current 5-min candle closed above OR high"""
        if not self.current_high:
            return False
        
        breakout = current_price > self.current_high
        if breakout:
            print(f"🚀 BREAKOUT! {self.ticker} ${current_price:.2f} > ${self.current_high:.2f}")
        
        return breakout


class WealthSeekerBot:
    """Main autonomous trading bot - Job C"""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.auditor = TradingAuditor()
        self.av_client = AlphaVantageClient()
        self.notifier = TelegramNotifier()
        self.executor = T212Executor()
        
        # Configuration
        self.watchlist = ["AAPL", "MSFT", "GOOGL"]  # Example tickers
        self.max_trades_per_day = 1
        self.trades_executed = 0
    
    def get_current_wealth(self) -> float:
        """Calculate total wealth from T212 account"""
        try:
            account = self.executor.get_account_info()
            return account.get("total", 0.0)
        except:
            return 1000.0  # Fallback to seed capital
    
    def run_orb_strategy(self, ticker: str) -> bool:
        """Execute ORB strategy for a single ticker"""
        print(f"\n{'='*60}")
        print(f"🎯 Analyzing {ticker} for ORB entry...")
        print(f"{'='*60}")
        
        # Step 1: Get opening range
        orb = ORBStrategy(ticker)
        orb_high = orb.fetch_opening_range()
        
        if not orb_high:
            print(f"❌ Could not establish opening range for {ticker}")
            return False
        
        # Step 2: Get current price
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.info.get('currentPrice', stock.info.get('regularMarketPrice', 0))
            
            if not current_price:
                print(f"❌ Could not fetch current price for {ticker}")
                return False
            
            print(f"💰 Current Price: ${current_price:.2f}")
        except Exception as e:
            print(f"❌ Price fetch failed: {e}")
            return False
        
        # Step 3: Check breakout condition
        if not orb.check_breakout(current_price):
            print(f"⏳ No breakout yet for {ticker}")
            return False
        
        # Step 4: VWAP filter
        vwap = self.av_client.get_vwap(ticker)
        if not vwap:
            print(f"⚠️  Could not fetch VWAP, skipping {ticker}")
            return False
        
        print(f"📈 VWAP: ${vwap:.2f}")
        
        if current_price <= vwap:
            print(f"❌ VWAP Filter Failed: ${current_price:.2f} <= ${vwap:.2f}")
            return False
        
        print(f"✅ VWAP Filter Passed: ${current_price:.2f} > ${vwap:.2f}")
        
        # Step 5: Calculate position size
        total_wealth = self.get_current_wealth()
        position_value = min(1000, total_wealth * 0.05)  # Will be validated by auditor
        shares = int(position_value / current_price)
        
        # Step 6: Run through the Gauntlet
        gauntlet_result = self.auditor.run_gauntlet(
            ticker=ticker,
            entry_price=current_price,
            position_size=position_value,
            total_wealth=total_wealth,
            daily_pnl=0.0,  # Would track throughout day
            news_context=f"ORB breakout detected for {ticker}"
        )
        
        print(f"\n🛡️  Gauntlet Result:")
        print(json.dumps(gauntlet_result, indent=2))
        
        if not gauntlet_result["approved"]:
            print(f"❌ Trade REJECTED: {gauntlet_result['reason']}")
            self.notifier.send_message(
                f"🚫 *Trade Rejected*\n"
                f"Ticker: {ticker}\n"
                f"Reason: {gauntlet_result['reason']}"
            )
            return False
        
        # Step 7: Execute trade
        if self.test_mode:
            print(f"🧪 TEST MODE: Would buy {shares} shares of {ticker} at ${current_price:.2f}")
            self.notifier.send_message(
                f"🧪 *TEST MODE Trade*\n"
                f"Ticker: {ticker}\n"
                f"Shares: {shares}\n"
                f"Price: ${current_price:.2f}\n"
                f"Value: £{position_value:.2f}"
            )
            return True
        
        try:
            order = self.executor.place_market_order(ticker, shares)
            print(f"✅ ORDER EXECUTED: {order}")
            
            self.notifier.send_message(
                f"✅ *Trade Executed*\n"
                f"Ticker: {ticker}\n"
                f"Shares: {shares}\n"
                f"Entry: ${current_price:.2f}\n"
                f"Value: £{position_value:.2f}\n"
                f"Strategy: ORB + VWAP\n"
                f"Order ID: {order.get('id', 'N/A')}"
            )
            
            self.trades_executed += 1
            return True
            
        except Exception as e:
            print(f"❌ ORDER FAILED: {e}")
            self.notifier.send_message(f"❌ *Order Failed*\nTicker: {ticker}\nError: {str(e)}")
            return False
    
    def run_autonomous(self):
        """Main autonomous execution loop"""
        print("\n" + "="*60)
        print("🤖 WEALTH SEEKER v0.01 - AUTONOMOUS MODE")
        print("="*60)
        print(f"⏰ Execution Time: {datetime.utcnow().isoformat()}Z")
        print(f"📊 Watchlist: {', '.join(self.watchlist)}")
        print(f"🧪 Test Mode: {'ENABLED' if self.test_mode else 'DISABLED'}")
        print("="*60 + "\n")
        
        # Scan watchlist for ORB opportunities
        for ticker in self.watchlist:
            if self.trades_executed >= self.max_trades_per_day:
                print(f"⚠️  Daily trade limit reached ({self.max_trades_per_day})")
                break
            
            success = self.run_orb_strategy(ticker)
            
            if success:
                print(f"✅ Successfully traded {ticker}")
            
            # Rate limiting
            time.sleep(2)
        
        print(f"\n{'='*60}")
        print(f"📊 Session Summary")
        print(f"{'='*60}")
        print(f"Trades Executed: {self.trades_executed}/{self.max_trades_per_day}")
        print(f"Completion Time: {datetime.utcnow().isoformat()}Z")
        print(f"{'='*60}\n")


def main():
    """Entry point for main_bot.py"""
    test_mode = "--test-mode" in sys.argv or "--autonomous" not in sys.argv
    
    if test_mode:
        print("🧪 Running in TEST MODE (no real trades)")
    
    bot = WealthSeekerBot(test_mode=test_mode)
    bot.run_autonomous()


if __name__ == "__main__":
    main()
