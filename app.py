"""
Flask Application - Sovereign Sentinel v1.9.1
==============================================

Dynamic Flask server replacing static HTML generation.
Serves Ghost Sovereign UI with live trade execution endpoint.

Routes:
- GET  /             Dashboard view (base.html)
- POST /api/execute_trade   Manual trade execution
- GET  /api/instruments     Search instrument database
"""

import json
import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timezone
from auditor import TradingAuditor
from data_mapper import (
    map_live_state_to_ui_context,
    load_instruments_for_search,
    get_inverted_color
)
from trading212_client import Trading212Client

# Initialize Flask app
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize services
auditor = TradingAuditor()
client = Trading212Client()


@app.route('/')
def dashboard():
    """
    Main dashboard view.
    Loads live_state.json and renders base.html with Ghost Sovereign UI.
    """
    try:
        # Generate fresh live state from auditor
        live_state = auditor.generate_live_state()
        
        # Map to UI context (preserves base.html compatibility)
        context = map_live_state_to_ui_context(live_state)
        
        # Render template
        return render_template('base.html', **context)
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return render_template('base.html', 
                             total_wealth=0.0,
                             cash=0.0,
                             session_pnl=0.0,
                             positions=[],
                             market_phase='ERROR',
                             connectivity_status='OFFLINE')


@app.route('/api/execute_trade', methods=['POST'])
def execute_trade():
    """
    Manual trade execution endpoint.
    
    Expected payload:
    {
        "ticker": "NVDA",
        "quantity": 10,
        "limit_price": 875.50,
        "side": "BUY"
    }
    
    Returns:
    {
        "success": true,
        "order_id": "...",
        "message": "Order placed successfully"
    }
    """
    try:
        data = request.json
        
        ticker = data.get('ticker')
        quantity = data.get('quantity')
        limit_price = data.get('limit_price')
        side = data.get('side', 'BUY')
        
        # Validate inputs
        if not all([ticker, quantity, limit_price]):
            return jsonify({
                'success': False,
                'message': 'Missing required fields: ticker, quantity, limit_price'
            }), 400
        
        # Get current state for gauntlet check
        live_state = auditor.generate_live_state()
        total_wealth = live_state.get('total_wealth', 0.0)
        
        # Calculate position size in GBP
        position_size = quantity * limit_price
        
        # Run through gauntlet (circuit breaker, position sizing, fact-check)
        gauntlet_result = auditor.run_gauntlet(
            ticker=ticker,
            entry_price=limit_price,
            position_size=position_size,
            total_wealth=total_wealth,
            daily_pnl=live_state.get('total_pnl', 0.0),
            news_context=""  # TODO: Fetch real-time news
        )
        
        if not gauntlet_result['approved']:
            return jsonify({
                'success': False,
                'message': f'Trade blocked by gauntlet: {gauntlet_result["reason"]}'
            }), 403
        
        # Execute trade via Trading 212
        order = client.place_limit_order(
            ticker=ticker,
            quantity=quantity,
            limit_price=gauntlet_result['normalized_price'],  # Use normalized price
            side=side
        )
        
        # Log trade for audit trail
        log_trade_execution(ticker, quantity, limit_price, side, order)
        
        return jsonify({
            'success': True,
            'order_id': order.get('id', 'unknown'),
            'message': f'PRE-ORDER SENT: {ticker} {quantity} @ £{limit_price}',
            'normalized_price': gauntlet_result['normalized_price']
        })
        
    except Exception as e:
        print(f"❌ Trade execution error: {e}")
        return jsonify({
            'success': False,
            'message': f'Execution failed: {str(e)}'
        }), 500


@app.route('/api/instruments', methods=['GET'])
def search_instruments():
    """
    Search instruments database for Manual Hub.
    
    Query params:
    - q: search query (ticker or company name)
    - isa_only: bool (default: false)
    
    Returns matching instruments from instruments.json
    """
    query = request.args.get('q', '').upper()
    isa_only = request.args.get('isa_only', 'false').lower() == 'true'
    
    instruments_data = load_instruments_for_search()
    instruments = instruments_data.get('instruments', [])
    
    # Filter by query
    if query:
        instruments = [
            i for i in instruments 
            if query in i['ticker'].upper() or query in i['company'].upper()
        ]
    
    # Filter by ISA eligibility
    if isa_only:
        instruments = [i for i in instruments if i.get('isa', False)]
    
    return jsonify({
        'count': len(instruments),
        'instruments': instruments[:50]  # Limit to 50 results
    })


def log_trade_execution(ticker: str, quantity: float, price: float, side: str, order_response: dict):
    """Log trade to audit CSV file"""
    log_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
        'ticker': ticker,
        'quantity': quantity,
        'price': price,
        'side': side,
        'order_id': order_response.get('id', 'unknown'),
        'status': order_response.get('status', 'unknown')
    }
    
    # Ensure logs directory exists
    os.makedirs('data/logs', exist_ok=True)
    
    # Append to CSV
    log_path = 'data/logs/trade_audit.csv'
    if not os.path.exists(log_path):
        # Create header
        with open(log_path, 'w') as f:
            f.write('timestamp,ticker,quantity,price,side,order_id,status\n')
    
    with open(log_path, 'a') as f:
        f.write(f"{log_entry['timestamp']},{ticker},{quantity},{price},{side},{log_entry['order_id']},{log_entry['status']}\n")
    
    print(f"📝 Trade logged: {ticker} {quantity} @ £{price}")


if __name__ == '__main__':
    # Development server
    # For production, use: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(host='0.0.0.0', port=5000, debug=True)
