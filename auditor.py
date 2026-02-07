"""
Wealth Seeker v0.01 - The Deterministic Gauntlet (auditor.py)
================================================================
Hard-coded decision logic to maximize reliability.
Generative AI is restricted to information extraction only.
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, Tuple
import os
import google.generativeai as genai


class TradingAuditor:
    """The Deterministic Gauntlet - All trading decisions flow through here."""
    
    def __init__(self):
        self.eod_balance_path = "data/eod_balance.json"
        self.daily_drawdown_limit = 1000.0  # £1,000 circuit breaker
        self.seed_capital = 1000.0
        self.scaling_threshold = 1000.0  # Unlock at £1,000 realized profit
        
        # Configure Gemini for fact-checking only
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def normalize_uk_price(self, ticker: str, raw_price: float) -> float:
        """
        Rule: Any asset with _UK_EQ in ticker or ending in .L is priced in pence.
        Action: normalized_price = raw_price / 100
        """
        is_uk_equity = "_UK_EQ" in ticker or ticker.endswith(".L")
        
        if is_uk_equity:
            return raw_price / 100.0
        return raw_price
    
    def load_balance_state(self) -> Dict[str, Any]:
        """Load current balance state from eod_balance.json"""
        try:
            with open(self.eod_balance_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  Balance file not found, using defaults")
            return {
                "realized_profit": 0.0,
                "seed_capital": 1000.0,
                "last_session": datetime.utcnow().strftime("%Y-%m-%d"),
                "scaling_unlocked": False,
                "total_trades": 0
            }
    
    def save_balance_state(self, state: Dict[str, Any]):
        """Persist balance state to disk"""
        with open(self.eod_balance_path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def calculate_max_position_size(self, total_wealth: float, realized_profit: float) -> float:
        """
        Gate 1 (Seed): If realized_profit < 1000, MAX_POSITION_SIZE = 1000
        Gate 2 (Growth): If realized_profit >= 1000, MAX_POSITION_SIZE = Total_Wealth * 0.05
        """
        if realized_profit < self.scaling_threshold:
            return self.seed_capital  # £1,000 seed lock
        else:
            return total_wealth * 0.05  # 5% of total wealth
    
    def check_circuit_breaker(self, daily_drawdown: float) -> bool:
        """
        Circuit Breaker: If Daily_Drawdown >= 1000, execute sys.exit()
        Returns True if breaker should trigger
        """
        if daily_drawdown >= self.daily_drawdown_limit:
            return True
        return False
    
    def fact_check_filter(self, ticker: str, news_context: str = "") -> Tuple[bool, Dict[str, bool]]:
        """
        Gemini Input: News, SEC Filings, Earnings Transcripts
        Gemini Output (Strict JSON): {"dividend_cut": bool, "earnings_today": bool, "ceo_resignation": bool}
        Logic: If any value is True, trade is HARD BLOCKED
        
        Returns: (is_blocked, fact_dict)
        """
        prompt = f"""
You are a financial fact-checker. Analyze the following information about {ticker}.

Context: {news_context if news_context else "No additional context provided"}

Extract ONLY these three facts as a JSON object:
{{
  "dividend_cut": <true if dividend was cut/suspended, false otherwise>,
  "earnings_today": <true if earnings are being reported today, false otherwise>,
  "ceo_resignation": <true if CEO resigned/was fired recently, false otherwise>
}}

Respond ONLY with valid JSON, no other text.
"""
        
        try:
            response = self.model.generate_content(prompt)
            fact_dict = json.loads(response.text.strip())
            
            # Hard block if any red flag is True
            is_blocked = any([
                fact_dict.get("dividend_cut", False),
                fact_dict.get("earnings_today", False),
                fact_dict.get("ceo_resignation", False)
            ])
            
            return is_blocked, fact_dict
            
        except Exception as e:
            print(f"⚠️  Fact-check failed for {ticker}: {e}")
            # Fail-safe: Block trade if fact-check fails
            return True, {"error": str(e)}
    
    def run_gauntlet(self, 
                     ticker: str,
                     entry_price: float,
                     position_size: float,
                     total_wealth: float,
                     daily_pnl: float,
                     news_context: str = "") -> Dict[str, Any]:
        """
        The Gauntlet: All trades must pass through this deterministic filter
        
        Returns dict with:
        - approved: bool
        - reason: str (if rejected)
        - normalized_price: float
        - max_position_size: float
        - fact_check: dict
        """
        result = {
            "approved": False,
            "reason": "",
            "ticker": ticker,
            "normalized_price": 0.0,
            "max_position_size": 0.0,
            "fact_check": {}
        }
        
        # Step 1: Normalize UK prices
        normalized_price = self.normalize_uk_price(ticker, entry_price)
        result["normalized_price"] = normalized_price
        
        # Step 2: Check circuit breaker
        daily_drawdown = abs(min(daily_pnl, 0))  # Negative P&L only
        if self.check_circuit_breaker(daily_drawdown):
            result["reason"] = f"CIRCUIT BREAKER: Daily drawdown £{daily_drawdown:.2f} >= £{self.daily_drawdown_limit}"
            return result
        
        # Step 3: Load balance state and calculate position limit
        balance_state = self.load_balance_state()
        realized_profit = balance_state.get("realized_profit", 0.0)
        max_position = self.calculate_max_position_size(total_wealth, realized_profit)
        result["max_position_size"] = max_position
        
        # Step 4: Validate position size
        if position_size > max_position:
            result["reason"] = f"Position size £{position_size:.2f} exceeds limit £{max_position:.2f}"
            return result
        
        # Step 5: Fact-check filter (Gemini integration)
        is_blocked, fact_dict = self.fact_check_filter(ticker, news_context)
        result["fact_check"] = fact_dict
        
        if is_blocked:
            result["reason"] = f"HARD BLOCKED by fact-check: {fact_dict}"
            return result
        
        # All checks passed
        result["approved"] = True
        result["reason"] = "All gauntlet checks passed"
        return result


def emergency_shutdown(reason: str):
    """Send Telegram alert and halt system"""
    import requests
    
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    message = f"🚨 EMERGENCY SHUTDOWN 🚨\n\n{reason}\n\nTimestamp: {datetime.utcnow().isoformat()}Z"
    
    if telegram_token and chat_id:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message})
    
    print(message)
    sys.exit(1)


if __name__ == "__main__":
    # Test the auditor
    auditor = TradingAuditor()
    
    # Test case: UK equity normalization
    test_ticker = "VOD.L"
    test_price = 7250  # 72.50 in pence
    normalized = auditor.normalize_uk_price(test_ticker, test_price)
    print(f"✅ UK Price Normalization Test: {test_price}p → £{normalized}")
    
    # Test case: Position sizing
    test_result = auditor.run_gauntlet(
        ticker="VOD.L",
        entry_price=7250,
        position_size=500,
        total_wealth=5000,
        daily_pnl=-50,
        news_context="Routine trading day, no major news"
    )
    
    print(f"\n✅ Gauntlet Test Result:")
    print(json.dumps(test_result, indent=2))
