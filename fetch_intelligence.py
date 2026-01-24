import json
import feedparser
import random
import yfinance as yf
from datetime import datetime

# ==============================================================================
# INTELLIGENCE ENGINE (PHASE 3: REAL DATA & SITREPS)
# ==============================================================================

def load_strategy():
    """Loads the Strategy Brain (strategy.json)."""
    try:
        with open('strategy.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Strategy Brain not found. Creating default.")
        return {"watchlist": [], "ghost_holdings": []}

def fetch_live_prices(strategy_data):
    """
    Fetches LIVE prices for Watchlist using yfinance.
    """
    print("   [INTEL] Connecting to Global Markets (yfinance)...")
    
    enriched_watchlist = []
    
    for item in strategy_data.get('watchlist', []):
        ticker = item['ticker']
        target = item.get('target_price', 0.0)
        
        # 1. Fetch Real Data
        try:
            stock = yf.Ticker(ticker)
            # fast_info is faster than .info, but .info has more "human" data
            # Let's try .history for price to be reliable
            hist = stock.history(period="1d")
            
            if not hist.empty:
                live_price = hist['Close'].iloc[-1]
            else:
                # Fallback if market closed/no data
                # Try regular info for 'currentPrice' or 'previousClose'
                info = stock.info
                live_price = info.get('currentPrice') or info.get('previousClose', target)
                
        except Exception as e:
            print(f"   [WARN] Failed to fetch {ticker}: {e}")
            live_price = target # Safety fallback to avoid breaking UI
        
        # 2. Logic (Distance Calculation)
        
        # --- TYPE SAFETY (CRASH PREVENTION) ---
        try:
            live_price = float(live_price)
        except (ValueError, TypeError):
            # If yfinance returns garbage, fallback to target to prevent crash
            print(f"   [WARN] Invalid price for {ticker}: {live_price}. Fallback to target.")
            live_price = float(target)

        # --- UNIVERSAL CURRENCY NORMALIZER ---
        # User confirmed: everything is in Pence.
        live_price /= 100.0
        target /= 100.0
        
        # (Live - Target) / Target
        distance_pct = ((live_price - target) / target) * 100
        
        # 3. Smart Status Update
        status = item['status']
        verdict = "WAIT"
        color = "text-neutral-400"

        if live_price < target:
            status = "BUY ZONE"
            verdict = "EXECUTE"
            color = "text-emerald-500"
        elif distance_pct < 2.0: # Within 2%
            status = "NEAR TARGET"
            verdict = "PREPARE"
            color = "text-amber-500"
        elif distance_pct > 50.0:
            verdict = "IGNORE"
            color = "text-neutral-600"
            
        enriched_watchlist.append({
            **item,
            'target_price': f"{target:.2f}", # Store normalized target for UI
            'live_price': f"{live_price:.2f}",
            'distance_pct': f"{distance_pct:+.2f}%",
            'verdict': verdict,
            'color': color,
            'status': status
        })
        
    strategy_data['watchlist'] = enriched_watchlist
    return strategy_data

def fetch_news(strategy_data):
    """
    Scans Google News RSS for Watchlist items.
    """
    print("   [INTEL] Intercepting News Signals...")
    
    if not strategy_data.get('watchlist'): return strategy_data
    
    # In Phase 3, we still keep this light to avoid rate limits, 
    # but we can enhance the logic if needed.
    
    keywords = ["Earnings", "Strike", "Dividend", "Acquisition", "Hike", "Split"]

    for item in strategy_data['watchlist']:
        # We'll stick to our synth/mock news for now unless we add a specific RSS parser
        # because raw RSS feeds are often messy.
        # But let's try to grab REAL news if we can via yfinance?
        # yfinance news is sometimes available.
        
        try:
            stock = yf.Ticker(item['ticker'])
            news = stock.news
            if news:
                latest = news[0]
                title = latest.get('title', 'No Signals')
                link = latest.get('link', '#')
                # Publisher
                pub = latest.get('publisher', 'Unknown')
                news_headline = f"{pub}: {title}"
                news_sentiment = "Realtime" # Placeholder for sentiment analysis
            else:
                raise ValueError("No news found")
        except:
             # Fallback to Synth if data fetch fails
            if "BUY ZONE" in item.get('status', ''):
                news_headline = f"Market undervalues {item['name']} (Analytic Model)."
                news_sentiment = "Bullish"
            else:
                news_headline = f"Monitoring {item['name']} price action."
                news_sentiment = "Neutral"
            
        item['news_headline'] = news_headline
        item['news_sentiment'] = news_sentiment

    return strategy_data

def generate_sitrep(data):
    """
    Generates the SITREP (Situation Report) based on the data.
    """
    # 1. Determine Time of Day
    hour_utc = datetime.utcnow().hour
    
    if hour_utc < 10:
        sitrep_type = "MORNING VALIDATOR"
        context = "London Open Analysis"
    elif hour_utc < 15:
        sitrep_type = "MACRO PIVOT"
        context = "US Pre-Market Scan"
    else:
        sitrep_type = "GLOBAL AUDITOR"
        context = "Closing Bell Report"
        
    # 2. Scan Targets
    actionable_intel = []
    for item in data.get('watchlist', []):
        if item['verdict'] in ['EXECUTE', 'PREPARE']:
            actionable_intel.append(f"{item['ticker']} is {item['status']} (Dist: {item['distance_pct']})")
            
    # 3. Construct Message
    timestamp = datetime.utcnow().strftime("%H:%M UTC")
    
    if actionable_intel:
        status_color = "text-emerald-500"
        headline = f"ACTION REQUIRED: {len(actionable_intel)} Targets Active"
        body = " // ".join(actionable_intel)
    else:
        status_color = "text-neutral-400"
        headline = "ALL QUIET. No targets in range."
        body = f"Monitoring {len(data.get('watchlist', []))} assets. Volatility nominal."

    sitrep = {
        "type": sitrep_type,
        "context": context,
        "timestamp": timestamp,
        "headline": headline,
        "body": body,
        "status_color": status_color
    }
    
    return sitrep

def run_intel():
    """Main Entry Point called by generate_static.py"""
    print("--- INTELLIGENCE ENGINE ONLINE (v3.0 - REAL DATA) ---")
    data = load_strategy()
    data = fetch_live_prices(data)
    data = fetch_news(data)
    
    # Generate SITREP
    sitrep = generate_sitrep(data)
    data['sitrep'] = sitrep
    
    print("--- INTEL GATHERED ---")
    return data
