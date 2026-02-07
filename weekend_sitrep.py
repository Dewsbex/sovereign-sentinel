"""
Wealth Seeker v0.01 - Weekend SITREP (weekend_sitrep.py)
=========================================================
Sunday Night Market Preview Script

Run this on Sunday evening to get Monday's market phase forecast,
sector targets, and trading preparation checklist.
"""

import json
from datetime import datetime, timedelta
from macro_clock import MacroClock
import os


def print_banner(text: str):
    """Print a formatted banner"""
    width = 70
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width + "\n")


def get_next_trading_day():
    """Calculate next Monday trading day"""
    now = datetime.utcnow()
    days_ahead = (7 - now.weekday()) % 7  # Days until Monday
    if days_ahead == 0:
        days_ahead = 7
    next_monday = now + timedelta(days=days_ahead)
    return next_monday


def print_market_phase_forecast(clock: MacroClock):
    """Display market phase and strategic implications"""
    print_banner("MACRO-CLOCK FORECAST")
    
    phase_data = clock.detect_market_phase()
    phase = phase_data["phase"]
    confidence = phase_data.get("confidence", 0.0)
    analysis = phase_data.get("analysis", "No analysis available")
    fortress_alert = phase_data.get("fortress_alert", False)
    
    print(f"📊 DETECTED PHASE:  {phase.replace('_', '-')}")
    print(f"📈 CONFIDENCE:      {confidence:.0%}")
    print(f"🧠 ANALYSIS:        {analysis}\n")
    
    if fortress_alert:
        print("⚠️  FORTRESS MIGRATION ALERT ⚠️")
        print("Defensive pivot recommended. Consider moving from Job C → Job A.\n")
    
    # Phase-specific strategy
    strategies = {
        "EARLY_BULL": {
            "bias": "AGGRESSIVE GROWTH",
            "job_c": "MAXIMIZE ORB volume (more tickers, higher frequency)",
            "job_a": "Target high-beta growth stocks with strong moats"
        },
        "MID_BULL": {
            "bias": "BALANCED MOMENTUM",
            "job_c": "Maintain ORB cadence, quality over quantity",
            "job_a": "Focus on industrials, materials, energy with pricing power"
        },
        "LATE_BULL": {
            "bias": "DEFENSIVE ROTATION",
            "job_c": "REDUCE ORB volume, tighten stops",
            "job_a": "Shift to healthcare, staples, utilities"
        },
        "BEAR": {
            "bias": "CAPITAL PRESERVATION",
            "job_c": "SUSPEND autonomous trading",
            "job_a": "Increase cash position, defensive positions only"
        }
    }
    
    strategy = strategies.get(phase, strategies["MID_BULL"])
    print(f"🎯 STRATEGIC BIAS:  {strategy['bias']}")
    print(f"   Job C (ORB):     {strategy['job_c']}")
    print(f"   Job A (Moat):    {strategy['job_a']}\n")


def print_sector_targets(clock: MacroClock, phase: str):
    """Display sector target allocations"""
    print_banner("SECTOR TARGET ALLOCATIONS")
    
    targets = clock.get_sector_targets(phase)
    
    print("Target weights for optimal phase alignment:\n")
    print(f"{'SECTOR':<30} {'TARGET WEIGHT':<15} {'RATIONALE'}")
    print("-" * 70)
    
    # Sort by target weight descending
    sorted_targets = sorted(targets.items(), key=lambda x: x[1], reverse=True)
    
    for sector, weight in sorted_targets[:6]:  # Top 6
        if weight > 0:
            print(f"{sector:<30} {weight:>6.1f}%")
    
    print()


def print_trading_checklist():
    """Display pre-trading checklist"""
    print_banner("MONDAY MORNING CHECKLIST")
    
    checklist = [
        ("API Connectivity", "Verify T212, Alpha Vantage, Gemini APIs"),
        ("Balance Sync", "Run: python sync_ledger.py"),
        ("ORB Candidates", "Review pre-market movers for Job C"),
        ("Circuit Breaker", "Confirm £1,000 drawdown limit active"),
        ("Seed Lock Status", "Check if scaling unlocked (profit >= £1000)"),
        ("Dashboard Live", "Verify Cloudflare Pages deployment"),
        ("Telegram Alerts", "Test notification delivery"),
        ("GitHub Actions", "Confirm workflow scheduled for 14:25 UTC")
    ]
    
    for i, (item, detail) in enumerate(checklist, 1):
        status = "[ ]"
        print(f"{status} {i}. {item:<20} → {detail}")
    
    print()


def print_market_hours():
    """Display key trading times"""
    print_banner("KEY TRADING WINDOWS (UTC)")
    
    next_monday = get_next_trading_day()
    
    print(f"📅 NEXT TRADING DAY: {next_monday.strftime('%A, %B %d, %Y')}\n")
    print(f"{'EVENT':<35} {'TIME (UTC)':<15}")
    print("-" * 50)
    print(f"{'GitHub Actions Trigger':<35} {'14:25':<15}")
    print(f"{'US Market Open (NY)':<35} {'14:30':<15}")
    print(f"{'ORB Setup Window (5-min)':<35} {'14:30-14:35':<15}")
    print(f"{'Active Trading Window':<35} {'14:35-21:00':<15}")
    print(f"{'Market Close (NY)':<35} {'21:00':<15}")
    print()


def print_risk_reminders():
    """Display risk management reminders"""
    print_banner("RISK MANAGEMENT REMINDERS")
    
    print("🛡️  THE GAUNTLET - 5 MANDATORY GATES:")
    print("   1. Pence Normalization (.L tickers ÷ 100)")
    print("   2. Circuit Breaker (£1000 drawdown = KILL)")
    print("   3. Seed Lock (Max £1000 until profitable)")
    print("   4. Scaling Gate (5% position sizing when unlocked)")
    print("   5. Fact-Check Filter (Gemini news validation)\n")
    
    print("⚠️  NEVER override the Gauntlet for any reason.")
    print("⚠️  If Circuit Breaker triggers, DO NOT resume trading same day.")
    print()


def load_current_state():
    """Load current portfolio state"""
    try:
        with open("data/eod_balance.json", 'r') as f:
            balance = json.load(f)
        
        with open("live_state.json", 'r') as f:
            live = json.load(f)
        
        return {**balance, **live}
    except FileNotFoundError:
        return {
            "total_wealth": 1000.0,
            "realized_profit": 0.0,
            "scaling_unlocked": False,
            "total_trades": 0
        }


def print_current_status():
    """Display current account status"""
    print_banner("CURRENT ACCOUNT STATUS")
    
    state = load_current_state()
    
    print(f"💰 TOTAL WEALTH:        £{state.get('total_wealth', 0):.2f}")
    print(f"💵 CASH AVAILABLE:      £{state.get('cash', 0):.2f}")
    print(f"📈 REALIZED PROFIT:     £{state.get('realized_profit', 0):.2f}")
    print(f"🔓 SCALING UNLOCKED:    {state.get('scaling_unlocked', False)}")
    print(f"📊 TOTAL TRADES:        {state.get('total_trades', 0)}")
    print(f"📍 POSITIONS:           {len(state.get('positions', []))}")
    print()
    
    # Position sizing guidance
    if state.get('scaling_unlocked', False):
        max_position = state.get('total_wealth', 0) * 0.05
        print(f"✅ SCALING ACTIVE: Max position size = £{max_position:.2f} (5% of wealth)")
    else:
        print(f"🔒 SEED LOCK ACTIVE: Max position size = £1000.00 (fixed)")
    print()


def main():
    """Generate Weekend SITREP"""
    
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  WEALTH SEEKER v0.01 - WEEKEND SITREP".center(68) + "█")
    print("█" + "  Sunday Night Market Intelligence Brief".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    print(f"\n⏰ Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
    
    # Initialize Macro-Clock
    clock = MacroClock()
    
    # 1. Current Status
    print_current_status()
    
    # 2. Market Phase Forecast
    phase_data = clock.detect_market_phase()
    print_market_phase_forecast(clock)
    
    # 3. Sector Targets
    print_sector_targets(clock, phase_data["phase"])
    
    # 4. Trading Hours
    print_market_hours()
    
    # 5. Pre-Trading Checklist
    print_trading_checklist()
    
    # 6. Risk Reminders
    print_risk_reminders()
    
    # Footer
    print("=" * 70)
    print("  GHOST SOVEREIGN - READY FOR AUTONOMOUS EXECUTION")
    print("  Next Action: Deploy at 14:25 UTC Monday")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
