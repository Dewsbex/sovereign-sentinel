#!/usr/bin/env python3
"""
Populate Strategic Holdings Blacklist
=====================================
Queries Trading212 for all current positions and creates the strategic holdings
blacklist by excluding any tickers in the session whitelist (today's purchases).

This ensures Job C (5% Sniper Bot) cannot touch long-term holdings.
"""

import json
import os
from datetime import datetime
from trading212_client import Trading212Client
from session_manager import SessionManager

def main():
    print("=" * 60)
    print("🛡️ STRATEGIC HOLDINGS BLACKLIST GENERATOR")
    print("=" * 60)
    
    # Initialize clients
    client = Trading212Client()
    session_mgr = SessionManager()
    
    # Get current positions from broker
    print("\n📊 Fetching current positions from Trading212...")
    positions = client.get_positions()
    
    if not positions:
        print("⚠️ No positions found in account.")
        return
    
    print(f"✅ Found {len(positions)} total positions")
    
    # Get session whitelist (today's purchases by Job C)
    session_whitelist = session_mgr.get_whitelist()
    print(f"📋 Session whitelist contains {len(session_whitelist)} tickers: {session_whitelist}")
    
    # Extract all position tickers
    all_tickers = []
    for pos in positions:
        ticker = pos.get('ticker', '')
        if ticker:
            all_tickers.append(ticker)
    
    # Strategic holdings = All positions - Session purchases
    strategic_holdings = [t for t in all_tickers if t not in session_whitelist]
    strategic_holdings.sort()
    
    print("\n" + "=" * 60)
    print("🎯 STRATEGIC HOLDINGS (TO BE PROTECTED)")
    print("=" * 60)
    for ticker in strategic_holdings:
        print(f"  • {ticker}")
    
    if session_whitelist:
        print("\n" + "=" * 60)
        print("✅ SESSION PURCHASES (ALREADY TRADEABLE BY JOB C)")
        print("=" * 60)
        for ticker in session_whitelist:
            print(f"  • {ticker}")
    
    # Create strategic holdings blacklist
    blacklist_path = "data/strategic_holdings.json"
    blacklist_data = {
        "last_updated": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "tickers": strategic_holdings,
        "notes": f"Auto-generated on {datetime.utcnow().strftime('%Y-%m-%d')}. These are Job A strategic holdings that Job C must NEVER touch.",
        "total_protected": len(strategic_holdings),
        "total_tradeable": len(session_whitelist)
    }
    
    # Save to disk
    with open(blacklist_path, 'w') as f:
        json.dump(blacklist_data, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"💾 Saved to: {blacklist_path}")
    print("=" * 60)
    print(f"✅ {len(strategic_holdings)} tickers PROTECTED from Job C")
    print(f"✅ {len(session_whitelist)} tickers TRADEABLE by Job C")
    print("\n🚀 You can now deploy this to the VPS!")

if __name__ == "__main__":
    main()
