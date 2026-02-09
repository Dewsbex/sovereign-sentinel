from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from trading212_client import Trading212Client
from auditor import TradingAuditor

app = Flask(__name__)

# Enable CORS for Cloudflare Pages deployment
CORS(app, origins=['https://sovereign-sentinel.pages.dev', 'http://localhost:8080'], supports_credentials=True)

# Paths
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "live_state.json")
EOD_BALANCE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "eod_balance.json")

# Sector target allocations (Macro-Clock)
SECTOR_TARGETS = {
    "Technology": 15.0,
    "Industrials": 18.0,
    "Materials": 15.0,
    "Energy": 15.0,
    "Financials": 12.0,
    "Consumer Discretionary": 10.0,
    "Healthcare": 8.0,
    "Consumer Staples": 5.0,
    "Utilities": 2.0,
    "Cash": 0.0
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/live_data')
def live_data():
    """Enhanced API endpoint providing full dashboard data"""
    try:
        # Initialize clients
        client = Trading212Client()
        auditor = TradingAuditor()
        
        # Fetch live data from Trading 212
        account_info = client.get_account_info()
        positions = client.get_positions()
        
        # Get account cash
        cash_data = client.get_account_summary()
        cash = float(cash_data.get('free', 0.0)) if cash_data else 0.0
        
        # Load balance state for realized profit
        balance_state = {}
        if os.path.exists(EOD_BALANCE_FILE):
            with open(EOD_BALANCE_FILE, 'r') as f:
                balance_state = json.load(f)
        
        realized_profit = balance_state.get('realized_profit', 0.0)
        
        # Calculate total wealth and session P/L
        total_invested = 0.0
        total_current_value = 0.0
        session_pnl = 0.0
        
        # Process positions and calculate sectors
        sectors = {}
        enriched_positions = []
        
        if isinstance(positions, list):
            for pos in positions:
                ticker = pos.get('ticker', '')
                quantity = pos.get('quantity', 0)
                avg_price = auditor.normalize_uk_price(ticker, pos.get('averagePrice', 0))
                current_price = auditor.normalize_uk_price(ticker, pos.get('currentPrice', 0))
                ppl = auditor.normalize_uk_price(ticker, pos.get('ppl', 0))
                
                invested = quantity * avg_price
                current_value = quantity * current_price
                
                total_invested += invested
                total_current_value += current_value
                session_pnl += ppl
                
                # Determine sector (simple heuristic - can be enhanced with instrument metadata)
                sector = get_sector_for_ticker(ticker)
                
                # Aggregate by sector
                if sector not in sectors:
                    sectors[sector] = {"value": 0.0, "tickers": [], "percent": 0.0}
                sectors[sector]["value"] += current_value
                sectors[sector]["tickers"].append(ticker)
                
                # Enrich position data
                enriched_positions.append({
                    "ticker": ticker.replace('_US_EQ', '').replace('_UK_EQ', ''),
                    "current_value": current_value,
                    "pnl": ppl,
                    "pnl_percent": (ppl / invested * 100) if invested > 0 else 0.0
                })
        
        # Add cash as a sector
        if cash > 0:
            sectors["Cash"] = {"value": cash, "tickers": ["CASH"], "percent": 0.0}
        
        # Calculate total wealth
        total_wealth = total_current_value + cash
        
        # Calculate sector percentages
        for sector in sectors:
            sectors[sector]["percent"] = (sectors[sector]["value"] / total_wealth * 100) if total_wealth > 0 else 0.0
        
        # Generate tactical brief
        tactical_brief = generate_tactical_brief(sectors, session_pnl, total_wealth)
        
        # Generate Job C targets (placeholder - can be enhanced with ORB data)
        job_c_targets = generate_job_c_targets()
        
        # Build response
        response = {
            "timestamp": account_info.get('timestamp', ''),
            "total_wealth": total_wealth,
            "cash": cash,
            "session_pnl": session_pnl,
            "realized_profit": realized_profit,
            "connectivity_status": "CONNECTED",
            "market_phase": determine_market_phase(session_pnl, total_wealth),
            "positions": enriched_positions,
            "sectors": sectors,
            "sector_targets": SECTOR_TARGETS,
            "tactical_brief": tactical_brief,
            "job_c_targets": job_c_targets
        }
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        error_msg = f"❌ Error generating live data: {e}\n{traceback.format_exc()}"
        print(error_msg)
        # Log to file
        with open(os.path.join(os.path.dirname(__file__), "server.log"), "a") as f:
            f.write(error_msg + "\n")
        # Fallback to file-based data
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                fallback_data = json.load(f)
                # Ensure it has required fields
                if "sectors" not in fallback_data:
                    fallback_data["sectors"] = {"Cash": {"percent": 100.0, "value": 0.0, "tickers": ["CASH"]}}
                if "sector_targets" not in fallback_data:
                    fallback_data["sector_targets"] = SECTOR_TARGETS
                if "tactical_brief" not in fallback_data:
                    fallback_data["tactical_brief"] = {"phase": "UNKNOWN", "assessment": "Data unavailable."}
                if "job_c_targets" not in fallback_data:
                    fallback_data["job_c_targets"] = []
                return jsonify(fallback_data)
        return jsonify({"error": str(e), "status": "OFFLINE"})

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

def generate_tactical_brief(sectors, session_pnl, total_wealth):
    """Generate AI tactical brief based on current portfolio state"""
    phase = determine_market_phase(session_pnl, total_wealth)
    
    # Identify overweight/underweight sectors
    analysis = []
    for sector, target in SECTOR_TARGETS.items():
        if sector not in sectors:
            continue
        current = sectors[sector]["percent"]
        delta = current - target
        if abs(delta) > 5:
            status = "overweight" if delta > 0 else "underweight"
            analysis.append(f"{sector} {status} by {abs(delta):.1f}%")
    
    assessment = f"**{phase} Market Phase** - Portfolio analysis: "
    if analysis:
        assessment += "; ".join(analysis[:3])
    else:
        assessment += "Portfolio allocation is balanced."
    
    return {
        "phase": phase,
        "assessment": assessment
    }

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
