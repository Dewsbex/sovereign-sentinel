"""
Data Mapper - Bridge for Flask/base.html Compatibility
=======================================================

Maps new backend data structures to the exact Jinja2 context that base.html expects.
This preserves the v1.4.1 Ghost Sovereign UI while enabling v1.9.1 backend architecture.
"""

import json
from typing import Dict, Any, List


def normalize_uk_price(ticker: str, value: float) -> float:
    """Apply /100 normalization to UK stocks (pence → pounds)"""
    if ticker.endswith('_UK_EQ') or ticker.endswith('.L'):
        return value / 100.0
    return value


def map_live_state_to_ui_context(live_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map auditor's live_state.json to base.html Jinja2 context.
    
    Expected base.html variables:
    - total_wealth
    - cash
    - session_pnl
    - positions (for heatmap)
    - market_phase
    - connectivity_status
    """
    
    # Extract holdings and sort by value (anti-sliver)
    holdings = live_state.get('holdings', [])
    holdings_sorted = sorted(holdings, key=lambda h: h.get('current_value', 0), reverse=True)
    
    # Calculate session P/L (difference from yesterday's close)
    session_pnl = live_state.get('total_pnl', 0.0)
    
    # Map to UI context
    context = {
        'total_wealth': live_state.get('total_wealth', 0.0),
        'cash': live_state.get('cash', 0.0),
        'session_pnl': session_pnl,
        'positions': holdings_sorted,
        'positions_count': len(holdings_sorted),
        'market_phase': determine_market_phase(session_pnl),
        'connectivity_status': 'LIVE',
        'timestamp': live_state.get('timestamp', ''),
        
        # Fortress stats (Sentinel Pot)
        'realized_pnl': 0.0,  # TODO: Fetch from eod_balance.json
        'sentinel_status': 'LOCKED',
        
        # Job C Sniper Candidates (placeholder until main_bot.py integration)
        'job_c_candidates': load_sniper_candidates()
    }
    
    return context


def determine_market_phase(session_pnl: float) -> str:
    """
    Simple market phase determination based on session P/L.
    TODO: Replace with Gemini AI analysis
    """
    if session_pnl > 100:
        return 'BULL_RUN'
    elif session_pnl > 0:
        return 'MID_BULL'
    elif session_pnl > -100:
        return 'MID_BEAR'
    else:
        return 'BEAR_TRAP'


def load_sniper_candidates() -> List[Dict[str, Any]]:
    """
    Load Job C sniper candidates.
    TODO: Replace with live yfinance data from main_bot.py
    """
    # Hardcoded placeholder for Phase 3
    return [
        {
            'ticker': 'NVDA',
            'status': 'WATCHING',
            'orb_high': 875.50,
            'target_entry': 878.30,
            'stop_loss': 870.20,
            'rvol': 1.8,
            'signal': 'MOMENTUM'
        },
        {
            'ticker': 'TSLA',
            'status': 'READY',
            'orb_high': 195.80,
            'target_entry': 196.75,
            'stop_loss': 192.50,
            'rvol': 2.1,
            'signal': 'BREAKOUT'
        }
    ]


def load_instruments_for_search() -> Dict[str, Any]:
    """Load instruments.json for Manual Hub search"""
    try:
        with open('data/instruments.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'metadata': {'count': 0}, 'instruments': []}


def get_inverted_color(pnl_percent: float) -> str:
    """
    Inverted Momentum Color Logic (Ghost Sovereign palette)
    Matches base.html expectations
    """
    if pnl_percent > 3.0:
        return '#bbf7d0'  # Mint Pastel (Breakout gain)
    elif pnl_percent > 0.1:
        return '#f0fdf4'  # Mint Tint (Noise gain)
    elif pnl_percent > -3.0:
        return '#fff1f2'  # Rose Tint (Noise loss)
    else:
        return '#fecaca'  # Rose Pastel (Breakout loss)
