"""
Wealth Seeker v0.01 - UI Generator (generate_ui.py)
===================================================
Generates static HTML dashboard with Macro-Clock and Industrial Vibe
"""

import json
import os
from datetime import datetime
from jinja2 import Template
from macro_clock import MacroClock


def get_inverted_color(pnl_percent: float) -> str:
    """
    Inverted Momentum Color Logic (LIGHT MODE - VIBE LAB):
    Small moves glow bright (pastels), large moves weigh heavy (deep solid)
    """
    if pnl_percent > 3.0:
        return '#166534'  # Forest Deep (High gain - heavy)
    elif pnl_percent > 1.0:
        return '#22c55e'  # Emerald Solid (Mid gain - solid)
    elif pnl_percent > 0.1:
        return '#dcfce7'  # Mint Pastel (Low gain - glowing)
    elif pnl_percent > -0.1:
        return '#fee2e2'  # Rose Pastel (Low loss - glowing)
    elif pnl_percent > -1.0:
        return '#ef4444'  # Crimson Solid (Mid loss - solid)
    elif pnl_percent > -3.0:
        return '#991b1b'  # Blood Deep (High loss - heavy)
    else:
        return '#7f1d1d'  # Deep Blood (Extreme loss - ultra heavy)


def load_state() -> dict:
    """Load live state from JSON files"""
    state = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_wealth": 0.0,
        "cash": 0.0,
        "session_pnl": 0.0,
        "positions": [],
        "pending_orders": [],
        "realized_profit": 0.0,
        "scaling_unlocked": False,
        "connectivity": "Unknown",
        "market_phase": "MID_BULL",
        "fortress_alert": False
    }
    
    # Load balance state
    try:
        with open("data/eod_balance.json", 'r') as f:
            balance = json.load(f)
            state.update(balance)
    except FileNotFoundError:
        print("⚠️  eod_balance.json not found")
    
    # Load live state if exists
    try:
        with open("live_state.json", 'r') as f:
            live_data = json.load(f)
            state.update(live_data)
    except FileNotFoundError:
        print("⚠️  live_state.json not found, using defaults")
    
    return state


def calculate_performance_data(positions: list) -> list:
    """Transform positions into heatmap data with inverted momentum colors"""
    heatmap_data = []
    
    for pos in positions:
        ticker = pos.get("ticker", "")
        pnl = pos.get("pnl", 0.0)
        pnl_percent = pos.get("pnl_percent", 0.0)
        value = pos.get("current_value", 0.0)
        
        heatmap_data.append({
            "x": ticker,
            "y": abs(pnl_percent),  # Size by absolute performance
            "color": get_inverted_color(pnl_percent),  # Inverted momentum color
            "ticker": ticker,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "value": value
        })
    
    return heatmap_data


def calculate_sector_allocation(positions: list, total_wealth: float, cash: float) -> dict:
    """Calculate sector weights including cash"""
    sectors = {}
    total_invested = sum(p.get("current_value", 0) for p in positions)
    
    # Add positions to sectors
    for pos in positions:
        sector = pos.get("sector", "Unknown")
        value = pos.get("current_value", 0)
        
        if sector not in sectors:
            sectors[sector] = {"value": 0, "tickers": []}
        
        sectors[sector]["value"] += value
        sectors[sector]["tickers"].append(pos.get("ticker", ""))
    
    # Add cash as separate sector
    if cash > 0:
        sectors["Cash"] = {"value": cash, "tickers": ["CASH"]}
    
    # Convert to percentages of total wealth
    for sector in sectors:
        sectors[sector]["percent"] = (sectors[sector]["value"] / total_wealth * 100) if total_wealth > 0 else 0
    
    return sectors


def calculate_sector_deltas(current_allocation: dict, market_phase: str) -> list:
    """
    Calculate delta between current allocation and Macro-Clock targets.
    Returns sorted list for bar chart visualization.
    """
    clock = MacroClock()
    targets = clock.get_sector_targets(market_phase)
    deltas = []
    
    for sector in targets:
        current_percent = current_allocation.get(sector, {}).get("percent", 0.0)
        target_percent = targets[sector]
        delta = current_percent - target_percent
        
        deltas.append({
            "sector": sector,
            "current": round(current_percent, 1),
            "target": round(target_percent, 1),
            "delta": round(delta, 1),
            "status": "OVER" if delta > 0.5 else "UNDER" if delta < - 0.5 else "MATCH"
        })
    
    # Sort by target weight (descending)
    deltas.sort(key=lambda x: x["target"], reverse=True)
    
    return deltas


def generate_dashboard(state: dict) -> str:
    """Generate HTML dashboard from state with Macro-Clock integration"""
    
    # Load template
    with open("templates/base.html", 'r', encoding='utf-8') as f:
        template_str = f.read()
    
    template = Template(template_str)
    
    # Get market phase
    clock = MacroClock()
    phase_data = clock.detect_market_phase()
    market_phase = phase_data["phase"]
    fortress_alert = phase_data.get("fortress_alert", False)
    
    # Prepare data
    heatmap_data = calculate_performance_data(state.get("positions", []))
    sectors = calculate_sector_allocation(
        state.get("positions", []),
        state.get("total_wealth", 0),
        state.get("cash", 0)
    )
    sector_deltas = calculate_sector_deltas(sectors, market_phase)
    
    # Render
    html = template.render(
        timestamp=state["timestamp"],
        total_wealth=state.get("total_wealth", 0),
        cash=state.get("cash", 0),
        session_pnl=state.get("session_pnl", 0),
        connectivity=state.get("connectivity", "Unknown"),
        market_phase=market_phase.replace("_", "-"),
        fortress_alert=fortress_alert,
        heatmap_data=json.dumps(heatmap_data),
        sectors=sectors,
        sector_deltas=sector_deltas,
        positions=state.get("positions", []),
        ai_brief=state.get("ai_strategic_brief", "_Strategic analysis pending..._"),
        orb_targets=state.get("orb_targets", [])
    )
    
    return html


def main():
    """Generate and save dashboard"""
    print("🎨 Generating Wealth Seeker Dashboard (Industrial Vibe)...")
    
    state = load_state()
    html = generate_dashboard(state)
    
    # Save to index.html
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard generated: index.html")
    print(f"   Total Wealth: £{state.get('total_wealth', 0):.2f}")
    print(f"   Positions: {len(state.get('positions', []))}")
    print(f"   Timestamp: {state['timestamp']}")


if __name__ == "__main__":
    main()
