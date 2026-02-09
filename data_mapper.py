"""
Data Mapper: The Lobotomy Bridge
=================================

Maps v1.9.1 backend structures (live_state.json) to base.html Jinja2 context.
Ensures UK price normalization and anti-sliver sorting.
"""

from typing import Dict, Any, List
import json
import os
from datetime import datetime, timezone


def normalize_uk_price(price: float, ticker: str) -> float:
    """
    Pence-Bug Fix: Normalize UK stock prices from pence to pounds.
    
    UK stocks (.L suffix or _UK_EQ cluster) are quoted in pence.
    Divide by 100 for proper display.
    """
    if ticker.endswith('.L') or '_UK_EQ' in ticker:
        return price / 100.0
    return price


def safe_get(obj: Any, key: str, default: Any = 0) -> Any:
    """Safely extract value from dict, ensuring no Undefined objects"""
    if obj is None:
        return default
    if isinstance(obj, dict):
        val = obj.get(key, default)
        # Check if it's a Jinja2 Undefined object
        if hasattr(val, '__class__') and 'Undefined' in val.__class__.__name__:
            return default
        return val
    return default


def map_live_state_to_ui_context(live_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map auditor's live_state.json to base.html Jinja2 context.
    """
    from macro_clock import MacroClock
    clock = MacroClock()
    phase_data = clock.detect_market_phase()
    
    # Extract holdings and sort by value (anti-sliver)
    holdings = safe_get(live_state, 'holdings', [])
    if not isinstance(holdings, list):
        holdings = []
    
    holdings_sorted = sorted(
        holdings, 
        key=lambda h: safe_get(h, 'current_value', 0), 
        reverse=True
    )
    
    # Calculate session P/L (difference from yesterday's close)
    session_pnl_raw = safe_get(live_state, 'total_pnl', 0.0)
    total_wealth_raw = safe_get(live_state, 'total_wealth', 0.0)
    
    # ========================================================================
    # v1.9.4 HEADER PENCE NORMALIZATION (CRITICAL FIX)
    # ========================================================================
    # Threshold: If total wealth > £100k, likely in pence (UK ISA seed is £1-5k)
    if total_wealth_raw > 100000:
        total_wealth_normalized = total_wealth_raw / 100.0
    else:
        total_wealth_normalized = total_wealth_raw
    
    # Session P/L: If absolute value > £1,000, likely in pence
    if abs(session_pnl_raw) > 1000:
        session_pnl_normalized = session_pnl_raw / 100.0
    else:
        session_pnl_normalized = session_pnl_raw
    
    # Map to UI context - ALL values must be Python primitives
    context = {
        'total_wealth': float(total_wealth_normalized),  # NORMALIZED
        'cash': float(safe_get(live_state, 'cash_available', 0.0)),
        'session_pnl': float(session_pnl_normalized),  # NORMALIZED
        'positions': holdings_sorted,
        'positions_count': len(holdings_sorted),
        'market_phase': phase_data['phase'],  # REAL MACRO-CLOCK
        'fortress_alert': phase_data.get('fortress_alert', False),
        'connectivity_status': str(safe_get(live_state, 'connectivity_status', 'READY')),
        'timestamp': str(safe_get(live_state, 'timestamp', datetime.now(timezone.utc).isoformat())),
        
        # Job C Sniper Candidates
        'job_c_candidates': load_sniper_candidates()
    }
    
    return context


def load_sniper_candidates() -> List[Dict[str, Any]]:
    """
    Load Job C sniper candidates from active bot state.
    """
    cache_path = 'data/orb_cache.json'
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


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
