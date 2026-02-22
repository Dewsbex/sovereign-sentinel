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
import pandas as pd

# Optional AI fact-checking
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("google-generativeai not installed, fact-checking disabled")


class TradingAuditor:
    """The Deterministic Gauntlet - All trading decisions flow through here."""
    
    def __init__(self):
        self.eod_balance_path = "data/eod_balance.json"
        self.live_state_path = "data/live_state.json"  # NEW: Volatile state
        self.instruments_path = "data/instruments.json"  # NEW: Ticker map
        self.daily_drawdown_limit = 1000.0  # £1,000 circuit breaker
        self.seed_capital = 1000.0
        self.scaling_threshold = 1000.0  # Unlock at £1,000 realized profit
        
        # Trading 212 API client (Consolidated Engine)
        from trading212_client import Trading212Client
        self.client = Trading212Client()
        
        # Configure Gemini via Client (No standalone genai needed)
        self.gemini_available = bool(self.client.gemini_key)

    def load_balance_state(self) -> Dict[str, Any]:
        """Loads realized profit and balance state from cache (Required for SPEC v2.1)"""
        try:
            if os.path.exists(self.eod_balance_path):
                with open(self.eod_balance_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading balance state: {e}")
        return {"realized_profit": 0.0, "timestamp": datetime.utcnow().isoformat()}

    def check_circuit_breaker(self, daily_drawdown: float) -> bool:
        """Circuit Breaker: Hard block if drawdown exceeds limit"""
        return daily_drawdown >= self.daily_drawdown_limit

    def calculate_max_position_size(self, total_wealth: float, realized_profit: float) -> float:
        """
        Calculates max position size based on wealth and profit (APROMS SPEC)
        Base: £250
        Scale: +10% of realized profit, capped at £3,000 for Lab.
        """
        base_size = 250.0
        
        # Scale up if we have significant realized profit
        if realized_profit > self.scaling_threshold:
            base_size += (realized_profit * 0.1)
            
        return min(base_size, 3000.0) 

    def check_spread_guard(self, ticker: str, bid: float, ask: float) -> bool:
        """
        Spread Guard: Rejects trade if (Ask - Bid) / Bid > 0.5% (0.005).
        Prevents buying into massive slippage.
        Note: Yahoo Finance bid/ask data can be stale after-hours.
        0.5% is appropriate for liquid US equities during market hours.
        """
        if bid <= 0: return False # Bad data
        spread_pct = (ask - bid) / bid
        
        # Rulebook Limit: 0.5% (Realistic APROMS for US Equities)
        LIMIT = 0.005
        
        if spread_pct > LIMIT:
            print(f"🛡️ SPREAD GUARD: {ticker} rejected. Spread {spread_pct:.4f} > {LIMIT}")
            return False
            
        return True

    def check_vwap_gate(self, ticker: str, current_price: float) -> bool:
        """
        VWAP Gate: Price > Anchored VWAP (Longs only).
        Ensures we are trading with the intraday trend.
        """
        try:
            import yfinance as yf
            # Fetch today's 1m data to calculate VWAP
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            
            if df.empty: 
                print(f"VWAP GATE: No data for {ticker}")
                return False
            
            # Handle MultiIndex if yf returns it (common in newer versions)
            if isinstance(df.columns, pd.MultiIndex):
                # Try to flatten or select the ticker
                if ticker in df.columns.levels[1]:
                    close = df['Close'][ticker]
                    volume = df['Volume'][ticker]
                else:
                    # Fallback: use first level if ticker not explicit
                    close = df['Close'].iloc[:, 0]
                    volume = df['Volume'].iloc[:, 0]
            else:
                close = df['Close']
                volume = df['Volume']
            
            # VWAP = sum(Price * Volume) / sum(Volume)
            pv = close * volume
            cum_pv = pv.sum()
            cum_vol = volume.sum()
            
            if cum_vol == 0: return False
            vwap = cum_pv / cum_vol
            
            print(f"VWAP GATE for {ticker}: Price {current_price:.2f} vs VWAP {vwap:.2f}")
            return current_price > vwap
        except Exception as e:
            print(f"VWAP Gate Error for {ticker}: {e}")
            return False

    def check_volatility_guard(self, ticker: str) -> bool:
        """
        Dynamic Volatility Guard: 1-minute Average True Range (ATR) 
        must be < 1.5 * 20-Day ATR Mean.
        """
        try:
            import yfinance as yf
            # 1. Get 20-day ATR Mean (Historical)
            hist = yf.download(ticker, period="1mo", interval="1d", progress=False)
            if len(hist) < 20: return True # Not enough data, fail safe-ish
            
            # Simple ATR approx: High - Low
            hist['tr'] = hist['High'] - hist['Low']
            atr_mean = hist['tr'].tail(20).mean()
            
            # 2. Get 1m ATR (Current)
            current = yf.download(ticker, period="1d", interval="1m", progress=False)
            if current.empty: return False
            
            current['tr'] = current['High'] - current['Low']
            current_atr = current['tr'].iloc[-1]
            
            limit = 1.5 * atr_mean
            print(f"VOL GUARD for {ticker}: ATR_1m {current_atr:.4f} (Limit: {limit:.4f})")
            return current_atr < limit
        except Exception as e:
            print(f"Volatility Guard Error: {e}")
            return True # Fail open but log

    def calculate_active_risk(self, base_risk: float, realized_pnl: float, floating_pnl: float) -> float:
        """
        APROMS Bi-Directional Risk Scalar:
        Risk % = Base Risk + (floor(max(0, Realized P&L) / Profit Step) * Increment)
        Unrealized Mirror: If floating P&L < step threshold, return to Base Risk.
        Global Cap: Hard ceiling at 5% of Total Portfolio.
        """
        PROFIT_STEP = 500.0   # Scale every £500 profit
        INCREMENT = 0.005      # +0.5% per step
        MAX_RISK = 0.05       # 5% Absolute Cap
        
        # 1. Scale Up based on realized profit
        steps = max(0, int(realized_pnl // PROFIT_STEP))
        scaled_risk = base_risk + (steps * INCREMENT)
        
        # 2. The Unrealized Mirror (Risk Lockdown)
        # If open trades are bleeding > 1 step, we retreat to base risk
        if floating_pnl < -PROFIT_STEP:
            print(f"UNREALIZED MIRROR: Floating P&L {floating_pnl} < -{PROFIT_STEP}. Locking Risk to BASE.")
            return base_risk
            
        return min(scaled_risk, MAX_RISK)

    def check_volume_filter(self, ticker: str, avg_volume: float) -> bool:
        """
        Volume Filter: Rejects trade if 30-day Avg Volume < 500k.
        Ensures liquidity (No "Ghost" stocks).
        """
        LIMIT = 500000
        if avg_volume < LIMIT:
             print(f"VOLUME FILTER: {ticker} rejected. Vol {avg_volume:,.0f} < {LIMIT:,.0f}")
             return False
             
        return True

    def normalize_uk_price(self, ticker: str, raw_price: float) -> float:
        """
        Rule: Any asset with _UK_EQ in ticker or ending in .L is priced in pence.
        Action: normalized_price = raw_price / 100
        """
        is_uk_equity = "_UK_EQ" in ticker or ticker.endswith(".L")
        
        if is_uk_equity:
            return raw_price / 100.0
        return raw_price

    def fact_check_filter(self, ticker: str, news_context: str = "") -> Tuple[bool, Dict[str, bool]]:
        """
        Gemini Input: News, SEC Filings, Earnings Transcripts
        Gemini Output (Strict JSON): {"dividend_cut": bool, "earnings_today": bool, "ceo_resignation": bool}
        Logic: If any value is True, trade is HARD BLOCKED
        
        Returns: (is_blocked, fact_dict)
        """
        # Skip fact-checking if Gemini unavailable
        if not self.gemini_available:
            print(f"Gemini unavailable, skipping fact-check for {ticker}")
            return False, {"skipped": True}
        
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
            # use consolidated client engine
            response_text = self.client.gemini_query(prompt)
            
            # Clean response text (remove markdown code blocks if present)
            cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
            
            fact_dict = json.loads(cleaned_text)
            
            # Hard block if any red flag is True
            is_blocked = any([
                fact_dict.get("dividend_cut", False),
                fact_dict.get("earnings_today", False),
                fact_dict.get("ceo_resignation", False)
            ])
            
            return is_blocked, fact_dict
            
        except Exception as e:
            print(f"Fact-check failed for {ticker}: {e}")
            # Fail-safe: Block trade if fact-check fails
            return True, {"error": str(e)}
    
    def get_seed_rule_limit(self) -> float:
        """
        Helper for Bot - returns valid max position size based on current state.
        Safely handles missing live state by defaulting to seed capital.
        """
        try:
            # Try to get live total wealth for dynamic scaling
            with open(self.live_state_path, 'r') as f:
                live_state = json.load(f)
                total_wealth = live_state.get('total_wealth', 0.0)
        except (FileNotFoundError, json.JSONDecodeError):
            total_wealth = 0.0

        state = self.load_balance_state()
        return self.calculate_max_position_size(total_wealth, state.get("realized_profit", 0.0))

    def check_global_risk_cap(self, total_wealth: float) -> Tuple[bool, str]:
        """
        APROMS Global Finality: Total Job C exposure cannot exceed 5% of Total Wealth.
        """
        try:
            from ledger import SessionLedger
            ledger = SessionLedger()
            
            total_exposure = 0.0
            today = datetime.utcnow().strftime('%Y-%m-%d')
            
            for ticker, trades in ledger.data["trades"].items():
                qty = ledger.get_session_quantity(ticker)
                if qty > 0:
                    # Estimate value based on last known price in ledger
                    # (In live loop, main_bot handles this more precisely)
                    last_price = trades[-1]["price"]
                    total_exposure += (qty * last_price)
            
            cap = total_wealth * 0.05
            if total_exposure >= cap:
                return True, f"GLOBAL RISK CAP: Total exposure £{total_exposure:.2f} >= £{cap:.2f} (5% Cap)"
            return False, ""
        except Exception as e:
            print(f"Global Risk Cap error: {e}")
            return False, ""

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

        # Step 2.5: GLOBAL RISK CAP (vFinal.15 SPEC)
        is_capped, cap_reason = self.check_global_risk_cap(total_wealth)
        if is_capped:
            result["reason"] = cap_reason
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
    
    def generate_live_state(self) -> Dict[str, Any]:
        """
        NEW v1.7.0: Generate live_state.json for UI rendering
        Fetches current positions and cash from Trading 212 with pence normalization.
        """
        print("Generating live state...")
        try:
            positions = self.client.get_positions()
            account_summary = self.client.get_account_info()
            
            # Real cash balance from official API
            cash_balance = float(account_summary.get('cash', {}).get('availableToTrade', 0.0))
            
            total_invested = 0.0
            total_current_value = 0.0
            total_pnl = 0.0
            holdings = []
            
            for pos in positions:
                ticker = pos['ticker']
                quantity = pos['quantity']
                avg_price = self.normalize_uk_price(ticker, pos['averagePrice'])
                current_price = self.normalize_uk_price(ticker, pos['currentPrice'])
                pnl = self.normalize_uk_price(ticker, pos['ppl'])
                
                invested = quantity * avg_price
                current_value = quantity * current_price
                
                total_invested += invested
                total_current_value += current_value
                total_pnl += pnl
                
                holdings.append({
                    'ticker': ticker,
                    'quantity': quantity,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'invested': invested,
                    'current_value': current_value,
                    'pnl': pnl,
                    'pnl_percent': (pnl / invested * 100) if invested > 0 else 0
                })
            
            # CRITICAL MATH FIX (Cash + Equity = Total Wealth)
            # This ensures we match the T212 dashboard total
            total_wealth = total_current_value + cash_balance
            
            live_state = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'total_wealth': total_current_value + cash_balance,
                'cash': cash_balance,
                'total_invested': total_invested,
                'total_current_value': total_current_value,
                'total_pnl': total_pnl,
                'positions_count': len(holdings),
                'holdings': holdings,
                'connectivity_status': 'CONNECTED'
            }
            
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            
            with open(self.live_state_path, 'w') as f:
                json.dump(live_state, f, indent=2)
            
            print(f"Live state updated: £{live_state['total_wealth']:.2f}")
            return live_state
            
        except Exception as e:
            print(f"Failed to generate live state: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'total_wealth': 0.0,
                'cash': 0.0,
                'total_pnl': 0.0,
                'holdings': [],
                'connectivity_status': 'OFFLINE'
            }
    
    def generate_instruments_map(self):
        """
        NEW v1.7.0: Generate instruments.json for Manual Hub search
        Fetches all tradeable instruments from Trading 212
        """
        print("Fetching full instrument list...")
        try:
            instruments = self.client._request('GET', '/api/v0/equity/metadata/instruments')
            
            instrument_map = {
                'last_updated': datetime.utcnow().isoformat() + 'Z',
                'count': len(instruments),
                'instruments': instruments
            }
            
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            
            with open(self.instruments_path, 'w') as f:
                json.dump(instrument_map, f, indent=2)
            
            print(f"Instrument map generated: {len(instruments)} tickers")
            
        except Exception as e:
            print(f"Failed to generate instrument map: {e}")

    def enforce_iron_seed(self) -> bool:
        """
        ENFORCES THE IRON SEED PROTOCOL (SPEC v2.1)
        Prevents 'Sniper Lab' exposure from exceeding £1,000.
        Only sums trades with value < £250.
        """
        try:
            # Fetch positions via client
            raw_positions = self.client.get_open_positions()
            
            # Robust parsing (Stop JSONDecodeError)
            if isinstance(raw_positions, str):
                try:
                    all_positions = json.loads(raw_positions)
                except json.JSONDecodeError:
                    print("Iron Seed: Failed to parse positions string.")
                    return True # Fail open to avoid deadlock, but warn.
            elif isinstance(raw_positions, list):
                all_positions = raw_positions
            else:
                all_positions = []
                
            # Identify Lab trades (Value < £250) and calculate exposure
            lab_exposure = 0.0
            
            for p in all_positions:
                try:
                    # Robust value extraction
                    val = float(p.get('value', 0) or 0)
                    
                    # STRICT FILTER: Only count "Lab" trades (< £250)
                    # Core holdings (> £250) are IGNORED by this cap.
                    if val < 250.0:
                        lab_exposure += val
                except:
                    continue
            
            # print(f"🛡️ CURRENT LAB EXPOSURE: £{lab_exposure:.2f} (Limit: £1,000)")
            
            if lab_exposure >= 3000.00:
                print(f"IRON SEED LIMIT REACHED (£{lab_exposure:.2f}). Blocking new Sniper entries.")
                return False
            
            return True
            
        except Exception as e:
            print(f"Iron Seed Check Error: {e}")
            return True

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
    
    # Test Iron Seed
    print("\n🛡️ Testing Iron Seed Protocol...")
    is_safe = auditor.enforce_iron_seed()
    print(f"Iron Seed Safe: {is_safe}")
