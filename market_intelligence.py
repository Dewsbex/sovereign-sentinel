import yfinance as yf
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os

# ==============================================================================
# MARKET INTELLIGENCE ENGINE (COMPREHENSIVE YFINANCE INTEGRATION)
# ==============================================================================

class MarketIntelligence:
    """
    Comprehensive market data provider using yfinance (100% free).
    
    Features:
    - Live stock prices with 52-week ranges
    - Dividend tracking and forecasting
    - Analyst ratings and target prices
    - Company fundamentals (sector, industry, market cap, P/E, ROIC)
    - ESG scores
    - News with sentiment
    - Historical data
    """
    
    def __init__(self, cache_duration_seconds=300):
        """
        Initialize with optional caching.
        
        Args:
            cache_duration_seconds: How long to cache ticker data (default 5 min)
        """
        self.cache = {}
        self.cache_duration = cache_duration_seconds
        self.cache_file = "data/market_intel_cache.json"
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk if available."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk."""
        os.makedirs(os.path.dirname(self.cache_file) or '.', exist_ok=True)
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except:
            pass
    
    def _is_cache_valid(self, ticker: str) -> bool:
        """Check if cached data is still valid."""
        if ticker not in self.cache:
            return False
        
        cache_time = self.cache[ticker].get('_cached_at', 0)
        age = time.time() - cache_time
        return age < self.cache_duration
    
    def get_comprehensive_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch all available free data for a ticker.
        
        Returns enriched dict with:
        - price_data: current, 52w high/low, etc.
        - dividends: yield, frequency, next payment
        - analyst_ratings: recommendations, target price
        - fundamentals: sector, industry, market cap, P/E, ROIC
        - esg_scores: environmental, social, governance
        - news: latest headlines with sentiment
        """
        # Check cache first
        if self._is_cache_valid(ticker):
            return self.cache[ticker]
        
        print(f"   [INTEL] Fetching comprehensive data for {ticker}...")
        
        try:
            stock = yf.Ticker(ticker)
            
            # Get all data in one go
            info = stock.info
            history_1d = stock.history(period="1d")
            history_1y = stock.history(period="1y")
            dividends = stock.dividends
            calendar = stock.calendar
            recommendations = stock.recommendations
            news = stock.news
            
            # Build comprehensive dataset
            data = {
                '_cached_at': time.time(),
                'ticker': ticker,
                'price_data': self._extract_price_data(info, history_1d, history_1y),
                'dividends': self._extract_dividend_data(info, dividends, calendar),
                'analyst_ratings': self._extract_analyst_data(info, recommendations),
                'fundamentals': self._extract_fundamentals(info),
                'esg_scores': self._extract_esg(info),
                'news': self._extract_news(news),
                'technical': self._extract_technical(history_1y)
            }
            
            # Cache it
            self.cache[ticker] = data
            self._save_cache()
            
            return data
            
        except Exception as e:
            print(f"   [WARN] Failed to fetch data for {ticker}: {e}")
            # Return minimal fallback data
            return self._get_fallback_data(ticker)
    
    def _extract_price_data(self, info: dict, hist_1d, hist_1y) -> dict:
        """Extract current price and 52-week range."""
        current_price = None
        if not hist_1d.empty:
            current_price = hist_1d['Close'].iloc[-1]
        else:
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        week_52_high = info.get('fiftyTwoWeekHigh', 0)
        week_52_low = info.get('fiftyTwoWeekLow', 0)
        
        # Calculate position in 52-week range (0-100%)
        range_position = 0
        if week_52_high and week_52_low and current_price:
            range_position = ((current_price - week_52_low) / (week_52_high - week_52_low)) * 100
        
        return {
            'current': current_price,
            'previous_close': info.get('previousClose'),
            'open': info.get('open'),
            'day_high': info.get('dayHigh'),
            'day_low': info.get('dayLow'),
            'week_52_high': week_52_high,
            'week_52_low': week_52_low,
            'range_position': range_position,
            'volume': info.get('volume'),
            'avg_volume': info.get('averageVolume')
        }
    
    def _extract_dividend_data(self, info: dict, dividends, calendar) -> dict:
        """Extract dividend information."""
        dividend_yield = info.get('dividendYield', 0)
        trailing_annual_dividend = info.get('trailingAnnualDividendRate', 0)
        payout_ratio = info.get('payoutRatio', 0)
        
        # Get dividend frequency
        div_frequency = "N/A"
        if not dividends.empty and len(dividends) >= 4:
            # Count dividends in last year
            one_year_ago = datetime.now() - timedelta(days=365)
            recent_divs = dividends[dividends.index > one_year_ago]
            div_count = len(recent_divs)
            
            if div_count >= 12:
                div_frequency = "Monthly"
            elif div_count >= 4:
                div_frequency = "Quarterly"
            elif div_count >= 2:
                div_frequency = "Semi-Annual"
            elif div_count >= 1:
                div_frequency = "Annual"
        
        # Next payment estimate (from calendar if available)
        next_payment = None
        next_payment_amount = None
        if calendar and 'Dividend Date' in calendar:
            try:
                next_payment = calendar['Dividend Date'].strftime('%Y-%m-%d')
                if 'Dividend' in calendar:
                    next_payment_amount = calendar['Dividend']
            except:
                pass
        
        return {
            'yield': dividend_yield,
            'annual_rate': trailing_annual_dividend,
            'payout_ratio': payout_ratio,
            'frequency': div_frequency,
            'next_payment_date': next_payment,
            'next_payment_amount': next_payment_amount,
            'ex_dividend_date': info.get('exDividendDate')
        }
    
    def _extract_analyst_data(self, info: dict, recommendations) -> dict:
        """Extract analyst ratings and target prices."""
        # Consensus recommendation (1=Strong Buy, 5=Sell)
        recommendation = info.get('recommendationKey', 'none')
        recommendation_mean = info.get('recommendationMean')
        
        # Target prices
        target_high = info.get('targetHighPrice')
        target_low = info.get('targetLowPrice')
        target_mean = info.get('targetMeanPrice')
        target_median = info.get('targetMedianPrice')
        
        # Count of analyst opinions
        num_analyst_opinions = info.get('numberOfAnalystOpinions', 0)
        
        # Parse recent recommendations
        recent_ratings = {'buy': 0, 'hold': 0, 'sell': 0}
        if recommendations is not None and not recommendations.empty:
            # Get last 3 months of recommendations
            three_months_ago = datetime.now() - timedelta(days=90)
            recent_recs = recommendations[recommendations.index > three_months_ago]
            
            for _, row in recent_recs.iterrows():
                action = str(row.get('To Grade', '')).lower()
                if any(word in action for word in ['buy', 'outperform', 'overweight']):
                    recent_ratings['buy'] += 1
                elif any(word in action for word in ['hold', 'neutral', 'equal']):
                    recent_ratings['hold'] += 1
                elif any(word in action for word in ['sell', 'underperform', 'underweight']):
                    recent_ratings['sell'] += 1
        
        return {
            'consensus': recommendation,
            'recommendation_mean': recommendation_mean,
            'target_high': target_high,
            'target_low': target_low,
            'target_mean': target_mean,
            'target_median': target_median,
            'num_analysts': num_analyst_opinions,
            'recent_ratings': recent_ratings
        }
    
    def _extract_fundamentals(self, info: dict) -> dict:
        """Extract company fundamentals."""
        return {
            'company_name': info.get('longName') or info.get('shortName'),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'country': info.get('country', 'Unknown'),
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'trailing_pe': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            'return_on_assets': info.get('returnOnAssets'),
            'return_on_equity': info.get('returnOnEquity'),
            'revenue': info.get('totalRevenue'),
            'revenue_per_share': info.get('revenuePerShare'),
            'quarterly_revenue_growth': info.get('revenueGrowth'),
            'gross_profit': info.get('grossProfits'),
            'free_cashflow': info.get('freeCashflow'),
            'operating_cashflow': info.get('operatingCashflow'),
            'earnings_growth': info.get('earningsGrowth'),
            'current_ratio': info.get('currentRatio'),
            'debt_to_equity': info.get('debtToEquity'),
            'book_value': info.get('bookValue'),
            'shares_outstanding': info.get('sharesOutstanding'),
            'float_shares': info.get('floatShares'),
            'beta': info.get('beta')
        }
    
    def _extract_esg(self, info: dict) -> dict:
        """Extract ESG scores if available."""
        return {
            'total_esg': info.get('esgScores', {}).get('totalEsg') if isinstance(info.get('esgScores'), dict) else None,
            'environment': info.get('esgScores', {}).get('environmentScore') if isinstance(info.get('esgScores'), dict) else None,
            'social': info.get('esgScores', {}).get('socialScore') if isinstance(info.get('esgScores'), dict) else None,
            'governance': info.get('esgScores', {}).get('governanceScore') if isinstance(info.get('esgScores'), dict) else None,
        }
    
    def _extract_news(self, news_items) -> List[dict]:
        """Extract and format news."""
        news_list = []
        if news_items:
            for item in news_items[:5]:  # Top 5 news items
                news_list.append({
                    'title': item.get('title'),
                    'publisher': item.get('publisher'),
                    'link': item.get('link'),
                    'published': item.get('providerPublishTime'),
                    'type': item.get('type')
                })
        return news_list
    
    def _extract_technical(self, history_1y) -> dict:
        """Calculate basic technical indicators."""
        if history_1y.empty:
            return {}
        
        # Calculate moving averages if we have enough data
        ma_50 = None
        ma_200 = None
        
        if len(history_1y) >= 50:
            ma_50 = history_1y['Close'].tail(50).mean()
        if len(history_1y) >= 200:
            ma_200 = history_1y['Close'].tail(200).mean()
        
        return {
            'ma_50': ma_50,
            'ma_200': ma_200,
        }
    
    def _get_fallback_data(self, ticker: str) -> dict:
        """Return minimal fallback data when fetch fails."""
        return {
            '_cached_at': time.time(),
            'ticker': ticker,
            'price_data': {'current': None},
            'dividends': {'yield': 0},
            'analyst_ratings': {'consensus': 'none'},
            'fundamentals': {'sector': 'Unknown', 'industry': 'Unknown'},
            'esg_scores': {},
            'news': [],
            'technical': {}
        }
    
    def get_bulk_prices(self, tickers: List[str]) -> Dict[str, float]:
        """
        Efficiently fetch current prices for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dict mapping ticker -> current price
        """
        prices = {}
        
        for ticker in tickers:
            # Use cache if available
            if self._is_cache_valid(ticker):
                cached = self.cache[ticker]
                price = cached.get('price_data', {}).get('current')
                if price:
                    prices[ticker] = price
                    continue
            
            # Fetch if not cached
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if not hist.empty:
                    prices[ticker] = hist['Close'].iloc[-1]
                else:
                    info = stock.info
                    prices[ticker] = info.get('currentPrice') or info.get('regularMarketPrice')
                
                time.sleep(0.3)  # Rate limiting
            except Exception as e:
                print(f"   [WARN] Failed to fetch price for {ticker}: {e}")
                prices[ticker] = None
        
        return prices


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def format_large_number(num: Optional[float]) -> str:
    """Format large numbers (market cap, revenue, etc.) to human-readable string."""
    if num is None:
        return "N/A"
    
    if num >= 1_000_000_000_000:
        return f"${num/1_000_000_000_000:.2f}T"
    elif num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"${num/1_000:.2f}K"
    else:
        return f"${num:.2f}"


def get_recommendation_label(key: str) -> str:
    """Convert recommendation key to human-readable label."""
    labels = {
        'strong_buy': 'STRONG BUY',
        'buy': 'BUY',
        'hold': 'HOLD',
        'sell': 'SELL',
        'strong_sell': 'STRONG SELL',
        'none': 'NO RATING'
    }
    return labels.get(key, key.upper())
