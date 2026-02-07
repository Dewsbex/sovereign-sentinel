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
    Inverted Momentum Color Logic (v1.0 - HIGH-KEY PASTELS):
    Breakout moves (>3%) use solid colors, noise uses pastels
    """
    if pnl_percent > 3.0:
        return '#bbf7d0'  # Soft Mint Pastel (Breakout gain)
    elif pnl_percent > 0.1:
        return '#f0fdf4'  # Visible Mint Tint (Noise gain)
    elif pnl_percent > -3.0:
        return '#fff1f2'  # Visible Rose Tint (Noise loss)
    else:
        return '#fecaca'  # Soft Rose Pastel (Breakout loss)





def get_sentinel_stats(state: dict) -> dict:
    """Extract Sentinel trading pot statistics (£1,000 seed lock)"""
    realized_profit = state.get("realized_profit", 0.0)
    scaling_unlocked = realized_profit >= 1000.0
    
    # Calculate current drawdown from seed
    seed_amount = 1000.0
    current_drawdown = seed_amount - realized_profit if realized_profit < 0 else 0.0
    
    return {
        "seed_amount": seed_amount,
        "realized_profit": realized_profit,
        "current_drawdown": current_drawdown,
        "scaling_unlocked": scaling_unlocked,
        "status": "UNLOCKED" if scaling_unlocked else "LOCKED",
        "total_trades": state.get("total_trades", 0)
    }


def get_t212_portfolio_data(state: dict) -> dict:
    """Extract full T212 portfolio data for analysis"""
    return {
        "total_wealth": state.get("total_wealth", 0.0),
        "cash": state.get("cash", 0.0),
        "positions": state.get("positions", []),
        "session_pnl": state.get("session_pnl", 0.0)
    }


def load_sentinel_ledger() -> dict:
    """Load Sentinel bot ledger for growth curve tracking"""
    try:
        with open("data/sentinel_ledger.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Initialize if doesn't exist
        ledger = {
            "seed_amount": 1000.00,
            "realized_profit": 0.00,
            "total_trades": 0,
            "status": "LOCKED",
            "history": [
                {
                    "date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "session_pnl": 0.00,
                    "cumulative_profit": 0.00,
                    "pot_value": 1000.00,
                    "trades_count": 0
                }
            ],
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        with open("data/sentinel_ledger.json", 'w') as f:
            json.dump(ledger, f, indent=2)
        return ledger


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
        "total_trades": 0,
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
    
    # Split data feeds
    sentinel_stats = get_sentinel_stats(state)
    t212_portfolio = get_t212_portfolio_data(state)
    sentinel_ledger = load_sentinel_ledger()
    
    print(f"📊 Data Feed Split:")
    print(f"   Sentinel Pot: Realized P/L = £{sentinel_stats['realized_profit']:.2f}")
    print(f"   T212 Portfolio: {len(t212_portfolio['positions'])} positions for heatmap")
    print(f"   Sentinel History: {len(sentinel_ledger['history'])} data points")
    
    # Prepare T212 portfolio analysis data (ALL HOLDINGS)
    heatmap_data = calculate_performance_data(t212_portfolio["positions"])
    sectors = calculate_sector_allocation(
        t212_portfolio["positions"],
        t212_portfolio["total_wealth"],
        t212_portfolio["cash"]
    )
    sector_deltas = calculate_sector_deltas(sectors, market_phase)
    
    # Render
    html = template.render(
        timestamp=state["timestamp"],
        # Sentinel Pot Stats
        sentinel=sentinel_stats,
        sentinel_ledger=sentinel_ledger,
        # T212 Portfolio Analysis
        total_wealth=t212_portfolio["total_wealth"],
        cash=t212_portfolio["cash"],
        session_pnl=t212_portfolio["session_pnl"],
        connectivity=state.get("connectivity", "Unknown"),
        market_phase=market_phase.replace("_", "-"),
        fortress_alert=fortress_alert,
        heatmap_data=json.dumps(heatmap_data),
        sectors=sectors,
        sector_deltas=sector_deltas,
        positions=t212_portfolio["positions"],
        ai_brief=state.get("ai_strategic_brief", "_Strategic analysis pending..._"),
        job_c_candidates=[
            {
                'ticker': 'TSLA',
                'orb_high': 245.50,
                'current': 242.75,
                'vwap_dist': '-1.2%',
                'atr': '3.80',
                'rvol': '1.45x',
                'status': 'READY',
                'signal': 'WAITING FOR BREAKOUT'
            },
            {
                'ticker': 'AMD',
                'orb_high': 178.20,
                'current': 176.80,
                'vwap_dist': '-0.8%',
                'atr': '2.15',
                'rvol': '2.10x',
                'status': 'READY',
                'signal': 'COILING AT VWAP'
            },
            {
                'ticker': 'NVDA',
                'orb_high': 620.10,
                'current': 625.30,
                'vwap_dist': '+0.5%',
                'atr': '8.40',
                'rvol': '1.85x',
                'status': 'ACTIVE',
                'signal': 'BREAKING ORB HIGH'
            }
        ]
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
