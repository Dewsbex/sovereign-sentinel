"""
Sniper List Intelligence - Live Watchlist Tracker
Uses yfinance to fetch real-time prices and calculate buy opportunities
"""
import json
import yfinance as yf
from datetime import datetime

def fetch_sniper_targets():
    """
    Reads watchlist.json and fetches live prices using yfinance.
    Returns enriched sniper list with distance to target and priority ranking.
    """
    try:
        with open('watchlist.json', 'r') as f:
            watchlist = json.load(f)
    except FileNotFoundError:
        print("[SNIPER] watchlist.json not found")
        return []
    except json.JSONDecodeError:
        print("[SNIPER] Invalid watchlist.json format")
        return []
    
    sniper_targets = []
    
    for item in watchlist:
        ticker = item.get('ticker')
        target_price = item.get('target_price', 0)
        expected_growth = item.get('expected_growth', 0)
        
        if not ticker:
            continue
        
        try:
            # Fetch live data from yfinance
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            
            # If still no price, try history
            if not current_price:
                hist = stock.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            # Calculate metrics
            distance_to_target = ((target_price - current_price) / current_price) * 100 if current_price > 0 else 0
            is_buy_signal = current_price <= target_price
            
            # Calculate expected return if bought at current price
            expected_return = expected_growth * 100  # Convert to percentage
            
            # Priority score: Higher is better
            # Factors: Distance below target (positive if below), expected growth
            priority_score = 0
            if is_buy_signal:
                priority_score = abs(distance_to_target) + expected_return
            else:
                priority_score = expected_return  # Still track but lower priority
            
            # Get additional data
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            market_cap = info.get('marketCap', 0)
            pe_ratio = info.get('trailingPE', 0)
            
            sniper_targets.append({
                'ticker': ticker,
                'name': info.get('shortName', ticker),
                'current_price': round(current_price, 2),
                'target_price': target_price,
                'distance_pct': round(distance_to_target, 2),
                'is_buy_signal': is_buy_signal,
                'expected_growth_pct': round(expected_return, 2),
                'priority_score': round(priority_score, 2),
                'sector': sector,
                'industry': industry,
                'market_cap': market_cap,
                'pe_ratio': round(pe_ratio, 2) if pe_ratio else None,
                'status': 'BUY NOW' if is_buy_signal else 'WATCH',
                'last_updated': datetime.utcnow().strftime('%H:%M UTC')
            })
            
        except Exception as e:
            print(f"[SNIPER] Failed to fetch {ticker}: {e}")
            # Add with error status
            sniper_targets.append({
                'ticker': ticker,
                'name': ticker,
                'current_price': 0,
                'target_price': target_price,
                'distance_pct': 0,
                'is_buy_signal': False,
                'expected_growth_pct': round(expected_growth * 100, 2),
                'priority_score': 0,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'market_cap': 0,
                'pe_ratio': None,
                'status': 'ERROR',
                'last_updated': datetime.utcnow().strftime('%H:%M UTC')
            })
    
    # Sort by priority score (highest first)
    sniper_targets.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return sniper_targets


def get_sector_data(ticker_raw):
    """
    Fetches real sector and industry data for a given ticker using yfinance.
    Returns dict with sector, industry, and other fundamentals.
    """
    try:
        # Clean ticker for yfinance (remove T212 suffixes)
        clean_ticker = ticker_raw.split('_')[0].replace('l_EQ', '')
        
        stock = yf.Ticker(clean_ticker)
        info = stock.info
        
        return {
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', 1.0),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0)
        }
    except Exception as e:
        print(f"[SECTOR] Failed to fetch data for {ticker_raw}: {e}")
        return {
            'sector': 'Unknown',
            'industry': 'Unknown',
            'market_cap': 0,
            'pe_ratio': 0,
            'dividend_yield': 0,
            'beta': 1.0,
            'fifty_two_week_high': 0,
            'fifty_two_week_low': 0
        }


if __name__ == "__main__":
    # Test the sniper list
    print("=" * 60)
    print("SNIPER LIST INTELLIGENCE TEST")
    print("=" * 60)
    
    targets = fetch_sniper_targets()
    
    print(f"\nFound {len(targets)} targets:\n")
    for t in targets:
        print(f"{t['ticker']:8} | £{t['current_price']:8.2f} -> £{t['target_price']:8.2f} | "
              f"{t['distance_pct']:+6.1f}% | {t['status']:10} | Priority: {t['priority_score']:.1f}")
