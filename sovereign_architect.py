"""
Sovereign Architect v27.0 Gold Master
Portfolio optimization engine with QELL filtering and actionable recommendations.
"""

import pandas as pd
import json
import os
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional
import yfinance as yf
from config import (
    RISK_FREE_RATE, STAMP_DUTY, US_WHT,
    TARGET_WEIGHT_CONVICTION, TARGET_WEIGHT_STANDARD,
    MIN_TRADE_SIZE_GBP, UK_FRICTION, US_FRICTION,
    YIELD_TRAP_THRESHOLD, PAYOUT_TRAP_THRESHOLD, PENNY_STOCK_THRESHOLD
)


class BionicTier(Enum):
    """AI/Automation capability tiers"""
    TIER_1_PLUS = "1+"  # Cyborg: Proven AI efficiency
    TIER_1 = "1"        # Sleeper: Structural AI fit
    TIER_2 = "2"        # Classic: Standard value


class PortfolioSegment(Enum):
    """Portfolio classification"""
    FORTRESS = "FORTRESS"  # Holdings to manage
    SNIPER = "SNIPER"      # New targets to buy
    RISK = "RISK"          # Toxic assets to liquidate


class SovereignArchitect:
    """
    Main analysis engine for portfolio optimization.
    Implements v27.0 Gold Master logic with QELL filtering.
    """
    
    def __init__(self):
        self.bionic_tiers = self._load_bionic_tiers()
        self.qell_history = self._load_qell_history()
        
    def _load_bionic_tiers(self) -> Dict:
        """Load Bionic Tier classifications from JSON"""
        try:
            with open('bionic_tiers.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("[ARCHITECT] Warning: bionic_tiers.json not found. Using defaults.")
            return {"tier_1_plus": {}, "tier_1": {}, "tier_2": {}}
    
    def _load_qell_history(self) -> Dict:
        """Load historical QELL scores"""
        history_path = 'data/qell_history.json'
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_qell_history(self):
        """Save QELL scores for historical tracking"""
        os.makedirs('data', exist_ok=True)
        with open('data/qell_history.json', 'w') as f:
            json.dump(self.qell_history, f, indent=2)
    
    def classify_bionic_tier(self, ticker: str, sector: str) -> BionicTier:
        """Determine Bionic Tier for a ticker"""
        # Check explicit classifications
        if ticker in self.bionic_tiers.get('tier_1_plus', {}):
            return BionicTier.TIER_1_PLUS
        if ticker in self.bionic_tiers.get('tier_1', {}):
            return BionicTier.TIER_1
        
        # Default to Tier 2
        return BionicTier.TIER_2
    
    def calculate_qell_score(self, ticker: str, ticker_data: Dict) -> Dict:
        """
        QELL Filtering: Quality, Earnings, Liquidity, Leverage
        Returns dict with individual scores and overall rating
        """
        scores = {
            'quality': 0,
            'earnings': 0,
            'liquidity': 0,
            'leverage': 0,
            'total': 0,
            'rating': 'FAIL'
        }
        
        try:
            # Fetch yfinance data
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Q - Quality: ROIC and Moat
            roic = info.get('returnOnAssets', 0)  # Proxy for ROIC
            if roic > 0.15:  # 15%+ ROA
                scores['quality'] = 2
            elif roic > 0.08:
                scores['quality'] = 1
            
            # E - Earnings: P/E vs historical average
            pe_current = ticker_data.get('pe_ratio', info.get('trailingPE', 0))
            pe_forward = info.get('forwardPE', 0)
            if pe_current > 0 and pe_forward > 0:
                if pe_current < pe_forward * 0.9:  # Trading below forward P/E
                    scores['earnings'] = 2
                elif pe_current < pe_forward * 1.1:
                    scores['earnings'] = 1
            
            # L - Liquidity: Market cap and volume
            market_cap = info.get('marketCap', 0)
            if market_cap > 10_000_000_000:  # £10B+
                scores['liquidity'] = 2
            elif market_cap > 1_000_000_000:  # £1B+
                scores['liquidity'] = 1
            
            # L - Leverage: Debt/Equity
            debt_to_equity = info.get('debtToEquity', 100)
            if debt_to_equity < 50:  # Low debt
                scores['leverage'] = 2
            elif debt_to_equity < 100:
                scores['leverage'] = 1
            
            # Calculate total
            scores['total'] = sum([
                scores['quality'],
                scores['earnings'],
                scores['liquidity'],
                scores['leverage']
            ])
            
            # Rating
            if scores['total'] >= 6:
                scores['rating'] = 'STRONG'
            elif scores['total'] >= 4:
                scores['rating'] = 'PASS'
            else:
                scores['rating'] = 'FAIL'
                
        except Exception as e:
            print(f"[QELL] Error calculating score for {ticker}: {e}")
        
        # Store in history
        timestamp = datetime.utcnow().isoformat()
        if ticker not in self.qell_history:
            self.qell_history[ticker] = []
        self.qell_history[ticker].append({
            'timestamp': timestamp,
            'scores': scores
        })
        
        return scores
    
    def calculate_target_weight(self, tier: BionicTier) -> float:
        """Calculate target portfolio weight based on tier"""
        if tier in [BionicTier.TIER_1_PLUS, BionicTier.TIER_1]:
            return TARGET_WEIGHT_CONVICTION  # 8%
        return TARGET_WEIGHT_STANDARD  # 5%
    
    def calculate_limit_price(self, target_price: float, is_uk: bool) -> float:
        """Apply friction math to target price"""
        friction = UK_FRICTION if is_uk else US_FRICTION
        return target_price / (1 + friction)
    
    def calculate_sizing(self, current_gbp: float, target_gbp: float, 
                        limit_price_gbp: float) -> Dict:
        """
        Calculate exact share quantity for buy/sell
        Returns action and sizing details
        """
        delta_gbp = target_gbp - current_gbp
        
        # Determine action
        if abs(delta_gbp) < MIN_TRADE_SIZE_GBP:
            return {
                'action': 'HOLD',
                'shares': 0,
                'value_gbp': 0,
                'reason': f'Delta £{abs(delta_gbp):.0f} < £{MIN_TRADE_SIZE_GBP} minimum'
            }
        
        if delta_gbp > 0:
            # Need to buy
            shares = int(delta_gbp / limit_price_gbp)
            return {
                'action': 'BUY',
                'shares': shares,
                'value_gbp': shares * limit_price_gbp,
                'reason': f'Underweight by £{delta_gbp:.0f}'
            }
        else:
            # Need to trim
            shares = int(abs(delta_gbp) / limit_price_gbp)
            return {
                'action': 'TRIM',
                'shares': shares,
                'value_gbp': abs(shares * limit_price_gbp),
                'reason': f'Overweight by £{abs(delta_gbp):.0f}'
            }
    
    def analyze_portfolio(self, csv_path: str = 'ISA_PORTFOLIO.csv') -> Dict:
        """
        Main analysis function.
        Reads CSV and returns segmented portfolio analysis.
        """
        print(f"\n{'='*60}")
        print("SOVEREIGN ARCHITECT v27.0 GOLD MASTER")
        print(f"{'='*60}\n")
        
        # Load CSV
        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            print(f"[ERROR] {csv_path} not found!")
            return self._empty_analysis()
        
        # Extract cash
        cash_row = df[df['Ticker'] == 'CASH_GBP']
        cash_balance = cash_row['Book Cost (£)'].iloc[0] if not cash_row.empty else 0
        
        # Get holdings (exclude cash)
        holdings_df = df[df['Status'] == 'Holding'].copy()
        
        # Calculate total portfolio value
        total_portfolio = holdings_df['Book Cost (£)'].sum() + cash_balance
        
        print(f"Total Portfolio: £{total_portfolio:,.2f}")
        print(f"Cash Balance: £{cash_balance:,.2f}")
        print(f"Holdings: {len(holdings_df)}\n")
        
        # Analyze each holding
        fortress = []
        risk_register = []
        
        for _, row in holdings_df.iterrows():
            ticker = row['Ticker']
            book_cost = row['Book Cost (£)']
            real_pl = row['Real P/L (£)']
            fx_impact = row['FX Impact (£)']
            
            # Clean ticker for yfinance
            clean_ticker = ticker.split('_')[0].replace('l_EQ', '')
            is_uk = '_UK_' in ticker or ticker.endswith('.L')
            
            # Classify
            tier = self.classify_bionic_tier(clean_ticker, "Unknown")
            qell = self.calculate_qell_score(clean_ticker, {
                'pe_ratio': row.get('Avg Price (Local)', 0)
            })
            
            # Check for toxic assets
            current_price = row.get('Live Price (Local)', 0)
            if current_price < PENNY_STOCK_THRESHOLD:
                risk_register.append({
                    'ticker': clean_ticker,
                    'red_flag': f'Penny Stock (£{current_price:.2f})',
                    'action': 'LIQUIDATE',
                    'current_value': book_cost
                })
                continue
            
            # Calculate target weight and sizing
            target_weight = self.calculate_target_weight(tier)
            target_gbp = total_portfolio * target_weight
            current_weight = book_cost / total_portfolio if total_portfolio > 0 else 0
            
            # Determine limit price
            target_price = current_price  # Simplified - would use valuation model
            limit_price = self.calculate_limit_price(target_price, is_uk)
            
            # Calculate sizing
            sizing = self.calculate_sizing(book_cost, target_gbp, limit_price)
            
            fortress.append({
                'ticker': clean_ticker,
                'tier': tier.value,
                'weight_current': current_weight,
                'weight_target': target_weight,
                'book_cost': book_cost,
                'real_pl': real_pl,
                'fx_impact': fx_impact,
                'qell_score': qell['total'],
                'qell_rating': qell['rating'],
                'action': sizing['action'],
                'shares': sizing['shares'],
                'value_gbp': sizing['value_gbp'],
                'reason': sizing['reason'],
                'limit_price': limit_price
            })
        
        # Save QELL history
        self._save_qell_history()
        
        # Build sniper list (from watchlist)
        sniper = self._build_sniper_list(total_portfolio, cash_balance)
        
        return {
            'fortress': fortress,
            'sniper': sniper,
            'risk': risk_register,
            'metrics': {
                'total_portfolio': total_portfolio,
                'cash_balance': cash_balance,
                'cash_hurdle': RISK_FREE_RATE,
                'num_holdings': len(fortress),
                'num_targets': len(sniper),
                'num_risks': len(risk_register)
            }
        }
    
    def _build_sniper_list(self, total_portfolio: float, cash_available: float) -> List[Dict]:
        """Build sniper list from watchlist.json"""
        try:
            with open('watchlist.json', 'r') as f:
                watchlist = json.load(f)
        except:
            return []
        
        sniper_targets = []
        for item in watchlist:
            ticker = item.get('ticker')
            target_price = item.get('target_price', 0)
            expected_growth = item.get('expected_growth', 0)
            
            # Classify tier
            tier = self.classify_bionic_tier(ticker, "Unknown")
            target_weight = self.calculate_target_weight(tier)
            target_gbp = total_portfolio * target_weight
            
            # Determine if UK or US
            is_uk = ticker.endswith('.L')
            limit_price = self.calculate_limit_price(target_price, is_uk)
            
            # Calculate shares
            shares = int(target_gbp / limit_price) if limit_price > 0 else 0
            
            sniper_targets.append({
                'ticker': ticker,
                'tier': tier.value,
                'target_price': target_price,
                'limit_price': limit_price,
                'target_weight': target_weight,
                'target_gbp': target_gbp,
                'shares': shares,
                'expected_growth': expected_growth
            })
        
        return sniper_targets
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            'fortress': [],
            'sniper': [],
            'risk': [],
            'metrics': {
                'total_portfolio': 0,
                'cash_balance': 0,
                'cash_hurdle': RISK_FREE_RATE,
                'num_holdings': 0,
                'num_targets': 0,
                'num_risks': 0
            }
        }


if __name__ == "__main__":
    # Test standalone
    architect = SovereignArchitect()
    analysis = architect.analyze_portfolio()
    
    print("\n[FORTRESS] Holdings")
    print("-" * 60)
    for holding in analysis['fortress']:
        print(f"{holding['ticker']:8} | {holding['action']:6} | "
              f"{holding['shares']:4} shares | £{holding['value_gbp']:,.0f}")
    
    print("\n[SNIPER] Targets")
    print("-" * 60)
    for target in analysis['sniper']:
        print(f"{target['ticker']:8} | Tier {target['tier']} | "
              f"{target['shares']:4} shares @ £{target['limit_price']:.2f}")
    
    print("\n[RISK] Register")
    print("-" * 60)
    for risk in analysis['risk']:
        print(f"{risk['ticker']:8} | {risk['red_flag']}")
