from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from trading212_client import Trading212Client
from auditor import TradingAuditor
from macro_clock import MacroClock
from datetime import datetime

app = Flask(__name__)

# Enable CORS for Cloudflare Pages deployment (including all preview/deployment URLs)
CORS(app, resources={r"/api/*": {"origins": [
    "https://sovereign-sentinel.pages.dev",
    "https://*.sovereign-sentinel.pages.dev",
    "http://localhost:8080",
    "http://localhost:5000"
]}}, supports_credentials=True)

# Paths
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "live_state.json")
EOD_BALANCE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "eod_balance.json")
EQUITY_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "equity_history.json")
SNIPER_TARGETS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "job_c_targets.json")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/live_data')
def live_data():
    """
    Enhanced API endpoint providing full dashboard data.
    Mapped strictly to Trading 212 Public API (v0) documentation.
    """
    try:
        # Initialize clients
        client = Trading212Client()
        auditor = TradingAuditor()
        clock = MacroClock()
        
        # 1. Fetch live data from Trading 212 with caching (20s)
        # Prevents "TooManyRequests" and stabilizes feed
        CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "api_cache.json")
        cache_valid = False
        cash_response = {}
        positions = []
        
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    if (datetime.utcnow() - datetime.fromisoformat(cache.get("timestamp", "2000-01-01"))).total_seconds() < 20:
                        cash_response = cache.get("cash", {})
                        positions = cache.get("positions", [])
                        cache_valid = True
                        # print("📦 Using cached API data")
            except: pass
            
        if not cache_valid:
            try:
                # print("🔄 Fetching fresh API data...")
                cash_response = client.get_account_summary()
                positions = client.get_positions()
                
                # Update cache
                try: 
                    with open(CACHE_FILE, 'w') as f:
                        json.dump({
                            "timestamp": datetime.utcnow().isoformat(),
                            "cash": cash_response,
                            "positions": positions
                        }, f)
                except: pass
                
            except Exception as api_error:
                print(f"⚠️ T212 API Error: {api_error}")
                # Fallback to persistent state
                if os.path.exists(STATE_FILE):
                    with open(STATE_FILE, 'r') as f:
                        cached_state = json.load(f)
                        return jsonify(cached_state)
                else:
                    return jsonify({"status": "OFFLINE", "error": "API unavailable"}), 503
        
        # 2. Extract Cash Metrics
        # Mapping: CASH = free (available to trade)
        cash = float(cash_response.get('free', 0.0)) if cash_response else 0.0
        
        # --- FIX: THE PENCE RULE ---
        # If cash is > 50,000, it is likely in pence. Normalize to pounds.
        if cash > 50000:
            cash = cash / 100.0
        
        # 3. Calculate Total Wealth from Positions
        # Formula: sum(quantity * currentPrice) for all positions + cash
        total_investments = 0.0
        session_pnl = 0.0
        sectors = {}
        enriched_positions = []
        
        if isinstance(positions, list):
            for pos in positions:
                ticker = pos.get('ticker', '')
                qty = float(pos.get('quantity', 0.0))
                
                # Normalize prices upfront
                avg_price = auditor.normalize_uk_price(ticker, pos.get('averagePrice', 0.0))
                current_price = auditor.normalize_uk_price(ticker, pos.get('currentPrice', 0.0))
                
                # Normalize PPL (Session P/L) if needed
                ppl = float(pos.get('ppl', 0.0))
                if abs(ppl) > 10000: # Sanity check for massive P/L
                    ppl = ppl / 100.0

                # Mapping: Heatmap Box Size = quantity * currentPrice
                box_size = qty * current_price
                
                # --- FIX: POSITION VALUE SANITY CHECK ---
                if box_size > 50000:
                    box_size = box_size / 100.0
                
                total_investments += box_size
                session_pnl += ppl
                
                # Mapping: Heatmap Color (Performance %) 
                # Formula: ((currentPrice - averagePrice) / averagePrice) * 100
                pnl_percent = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0.0
                
                # Determine sector (local logic or database)
                sector = get_sector_for_ticker(ticker)
                
                # Aggregate by sector
                if sector not in sectors:
                    sectors[sector] = {"value": 0.0, "tickers": [], "percent": 0.0}
                sectors[sector]["value"] += box_size
                sectors[sector]["tickers"].append(ticker)
                
                # Enrich position data for Heatmap
                enriched_positions.append({
                    "ticker": ticker.replace('_US_EQ', '').replace('_UK_EQ', ''),
                    "current_value": box_size,
                    "pnl": ppl,
                    "pnl_percent": pnl_percent
                })
        
        # WEALTH = Investments + Cash
        total_wealth = total_investments + cash
        
        # 4. Extract Realized Profit (from historical data if available)
        # Note: T212 API doesn't provide realized P/L in real-time
        # This would need to be tracked separately or calculated from transaction history
        realized_profit = 0.0  # Placeholder - requires transaction history analysis
        
        # Add cash as a sector for Asset Mix donut
        if cash > 0:
            sectors["Cash"] = {"value": cash, "tickers": ["CASH"], "percent": 0.0}
        
        # Calculate sector percentages relative to Total Wealth
        for sector in sectors:
            sectors[sector]["percent"] = (sectors[sector]["value"] / total_wealth * 100) if total_wealth > 0 else 0.0
        
        # 5. Macro-Clock Phase and Targets
        try:
            phase_data = clock.detect_market_phase()
            market_phase = phase_data["phase"]
            sector_targets = clock.get_sector_targets(market_phase)
        except Exception as clock_error:
            print(f"⚠️ MacroClock Error: {clock_error}")
            market_phase = "MID-BULL"
            sector_targets = {}
            phase_data = {"analysis": "MacroClock data unavailable."} # Define phase_data for tactical brief
        
        # Generate tactical brief
        tactical_brief = generate_tactical_brief(sectors, session_pnl, total_wealth, sector_targets, phase_data.get("analysis", "") if 'phase_data' in locals() else "")
        
        # Job C Sniper Targets (Read from main_bot.py output)
        job_c_targets = []
        if os.path.exists(SNIPER_TARGETS_FILE):
             try:
                 with open(SNIPER_TARGETS_FILE, 'r') as f:
                     job_c_targets = json.load(f)
             except: pass
        
        # 6. Persistent Equity Curve Logging
        log_equity_curve(total_wealth)
        equity_history = []
        if os.path.exists(EQUITY_HISTORY_FILE):
             try:
                 with open(EQUITY_HISTORY_FILE, 'r') as f:
                     equity_history = json.load(f)
             except: pass
        
        # Build strict response object
        response = {
            "timestamp": datetime.now().isoformat() + "Z",
            "total_wealth": total_wealth,
            "session_pnl": session_pnl,
            "realized_profit": realized_profit,
            "cash": cash,
            "connectivity_status": "LIVE",
            "market_phase": market_phase,
            "positions": enriched_positions,
            "sectors": sectors,
            "sector_targets": sector_targets,
            "tactical_brief": tactical_brief,
            "job_c_targets": job_c_targets,
            "equity_history": equity_history[-50:] # Last 50 points
        }
        
        # Save persistent state for fallback
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, 'w') as f:
                json.dump(response, f, indent=2)
        except Exception as e:
            print(f"⚠️ State persistence error: {e}")
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        error_msg = f"❌ Error generating live data: {e}\n{traceback.format_exc()}"
        print(error_msg)
        try:
            with open(os.path.join(os.path.dirname(__file__), "server.log"), "a") as f:
                f.write(error_msg + "\n")
        except: pass
        
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                fallback_data = json.load(f)
                fallback_data["connectivity_status"] = "OFFLINE"
                return jsonify(fallback_data)
        return jsonify({"error": str(e), "status": "OFFLINE"})

def save_live_state(data):
    """Saves current state to data/live_state.json for Job A/C persistence"""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save live state: {e}")

def log_equity_curve(total_wealth):
    """Logs total wealth over time for the equity curve chart"""
    try:
        os.makedirs(os.path.dirname(EQUITY_HISTORY_FILE), exist_ok=True)
        history = []
        if os.path.exists(EQUITY_HISTORY_FILE):
            with open(EQUITY_HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        # Log if value changed or every hour
        now = datetime.now().isoformat()
        if not history or history[-1]["value"] != total_wealth:
             history.append({"timestamp": now, "value": total_wealth})
             with open(EQUITY_HISTORY_FILE, 'w') as f:
                 json.dump(history[-1000:], f)
    except Exception as e: print(f"⚠️ Equity log error: {e}")

def get_sector_for_ticker(ticker):
    """Simple sector mapping - can be enhanced with Trading212 instrument metadata"""
    sector_map = {
        "AAPL": "Technology",
        "MSFT": "Technology",
        "NVDA": "Technology",
        "GOOGL": "Technology",
        "META": "Technology",
        "AMZN": "Consumer Discretionary",
        "TSLA": "Consumer Discretionary",
        "JNJ": "Healthcare",
        "PFE": "Healthcare",
        "UNH": "Healthcare",
        "XOM": "Energy",
        "CVX": "Energy",
        "COP": "Energy",
        "JPM": "Financials",
        "BAC": "Financials",
        "WFC": "Financials",
        "CAT": "Industrials",
        "BA": "Industrials",
        "HON": "Industrials",
        "PG": "Consumer Staples",
        "KO": "Consumer Staples",
        "WMT": "Consumer Staples",
        "NEE": "Utilities",
        "DUK": "Utilities",
        "SO": "Utilities",
        "FCX": "Materials",
        "NEM": "Materials",
        "LIN": "Materials"
    }
    
    clean_ticker = ticker.replace('_US_EQ', '').replace('_UK_EQ', '')
    return sector_map.get(clean_ticker, "Other")

def determine_market_phase(session_pnl, total_wealth):
    """Determine market phase based on portfolio performance"""
    if session_pnl > total_wealth * 0.02:
        return "STRONG-BULL"
    elif session_pnl > total_wealth * 0.005:
        return "MID-BULL"
    elif session_pnl > -total_wealth * 0.005:
        return "NEUTRAL"
    elif session_pnl > -total_wealth * 0.02:
        return "MID-BEAR"
    else:
        return "STRONG-BEAR"

BRIEF_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "tactical_brief_cache.json")

def generate_tactical_brief(sectors, session_pnl, total_wealth, sector_targets, ai_analysis=""):
    """
    Generate Tactical Brief with caching to conserve tokens and reduce jitter.
    Updates primarily on Macro-Clock changes or significant P/L shifts (every 4 hours max).
    """
    # 1. Check Cache
    try:
        if os.path.exists(BRIEF_CACHE_FILE):
            with open(BRIEF_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            # Check age (4 hours = 6 times/day, relaxed to user's "3 times" request -> 8 hours)
            cached_time = datetime.fromisoformat(cache.get("timestamp", "2000-01-01"))
            if (datetime.utcnow() - cached_time).total_seconds() < 8 * 3600:
                return cache.get("brief", {})
    except Exception as e:
        print(f"⚠️ Tactical Brief cache read error: {e}")

    # 2. Generate Fresh Brief (if cache stale)
    phase = determine_market_phase(session_pnl, total_wealth)
    
    # Identify overweight/underweight sectors based on Clock targets
    analysis = []
    for sector, target in sector_targets.items():
        current = sectors.get(sector, {}).get("percent", 0.0)
        delta = current - target
        if abs(delta) > 5:
            status = "overweight" if delta > 0 else "underweight"
            analysis.append(f"{sector} {status} by {abs(delta):.1f}%")
    
    assessment = f"**{phase} Market Phase** - {ai_analysis} "
    if analysis:
        assessment += "<br><br>**Portfolio Deltas:** " + "; ".join(analysis[:3])
    else:
        assessment += "<br><br>Portfolio allocation is balanced relative to Macro-Clock."
    
    brief = {
        "phase": phase,
        "assessment": assessment
    }
    
    # 3. Save to Cache
    try:
        os.makedirs(os.path.dirname(BRIEF_CACHE_FILE), exist_ok=True)
        with open(BRIEF_CACHE_FILE, 'w') as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "brief": brief
            }, f, indent=2)
    except Exception as e:
        print(f"⚠️ Tactical Brief cache write error: {e}")
        
    return brief

def generate_job_c_targets():
    """Generate Job C sniper targets - placeholder for ORB integration"""
    # This would ideally pull from main_bot.py ORB data or a shared state file
    # For now, return empty array - can be enhanced later
    return [
        {
            "ticker": "TSLA",
            "status": "READY",
            "orb_high": 245.50,
            "target": 245.88,
            "stop_loss": 239.80,
            "rvol": 1.45,
            "signal": "WAITING FOR BREAKOUT"
        }
    ]

@app.route('/api/execute', methods=['POST'])
def execute_trade():
    """Execute sniper trade via Trading 212 API"""
    data = request.json
    ticker = data.get('ticker')
    price = data.get('price')
    
    print(f"⚡ SNIPER COMMAND RECEIVED: {ticker} @ ${price}")
    
    try:
        client = Trading212Client()
        auditor = TradingAuditor()
        
        # Get max position size from auditor
        max_position = auditor.get_seed_rule_limit()
        
        # Calculate quantity based on max position and price
        quantity = int(max_position / price)
        
        if quantity <= 0:
            return jsonify({"status": "REJECTED", "message": "Insufficient capital for trade"})
        
        # Place limit order
        result = client.place_limit_order(ticker, quantity, price, side='BUY')
        
        if result.get('status') == 'FAILED':
            return jsonify({"status": "FAILED", "message": result.get('error', 'Unknown error')})
        
        # Send Telegram alert
        alert = f"🎯 SNIPER EXECUTED\n\nBUY {ticker} @ ${price}\nQuantity: {quantity}"
        client.send_telegram(alert)
        
        return jsonify({"status": "SUCCESS", "message": f"Order placed: BUY {quantity} {ticker} @ ${price}"})
        
    except Exception as e:
        print(f"❌ Trade execution failed: {e}")
        return jsonify({"status": "ERROR", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
