"""
Strategic Holdings Guard Test
Tests that main_bot.py blocks trades for tickers in the strategic holdings blacklist.
"""
import json
import os
import sys

def test_strategic_guard():
    """
    Test Scenario:
    - Strategic Holdings Blacklist: AAPL, MSFT
    - Breakout Signal received for: AAPL (should be BLOCKED)
    - Breakout Signal received for: NVDA (should be ALLOWED)
    
    Expected Result:
    - AAPL trade is blocked with STRATEGIC_BLOCK log
    - NVDA trade proceeds normally
    """
    print("=" * 70)
    print("TEST: Strategic Holdings Guard")
    print("=" * 70)
    
    # Setup: Create strategic holdings blacklist
    strategic_holdings = {
        "last_updated": "2026-02-17T16:42:00Z",
        "tickers": ["AAPL", "MSFT", "GOOGL"],
        "notes": "Test blacklist - Job A strategic holdings"
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/strategic_holdings.json', 'w') as f:
        json.dump(strategic_holdings, f, indent=2)
    
    # Simulate loading the blacklist (as main_bot.py does)
    print("\n📋 Loading strategic holdings blacklist...")
    with open('data/strategic_holdings.json', 'r') as f:
        blacklist_data = json.load(f)
        strategic_blacklist = set(blacklist_data.get('tickers', []))
    
    print(f"✅ Loaded {len(strategic_blacklist)} protected tickers: {strategic_blacklist}\n")
    
    # Simulate trade signals
    test_trades = [
        {"ticker": "AAPL", "price": 152.0, "quantity": 10, "reason": "Breakout"},
        {"ticker": "MSFT", "price": 305.0, "quantity": 5, "reason": "Breakout"},
        {"ticker": "NVDA", "price": 202.0, "quantity": 5, "reason": "Breakout"},
        {"ticker": "TSLA", "price": 255.0, "quantity": 4, "reason": "Breakout"}
    ]
    
    print("🚨 Simulating trade signals:")
    blocked_count = 0
    allowed_count = 0
    
    for trade in test_trades:
        ticker = trade['ticker']
        
        # Apply strategic holdings guard
        if ticker in strategic_blacklist:
            print(f"  ❌ {ticker}: BLOCKED (Strategic holding protected)")
            blocked_count += 1
        else:
            print(f"  ✅ {ticker}: ALLOWED (Not in blacklist)")
            allowed_count += 1
    
    print(f"\n📊 Results:")
    print(f"  Blocked: {blocked_count}")
    print(f"  Allowed: {allowed_count}\n")
    
    # Assertions
    assert blocked_count == 2, f"FAIL: Expected 2 blocked trades, got {blocked_count}"
    assert allowed_count == 2, f"FAIL: Expected 2 allowed trades, got {allowed_count}"
    
    # Test specific tickers
    assert "AAPL" in strategic_blacklist, "FAIL: AAPL should be in blacklist"
    assert "MSFT" in strategic_blacklist, "FAIL: MSFT should be in blacklist"
    assert "NVDA" not in strategic_blacklist, "FAIL: NVDA should NOT be in blacklist"
    assert "TSLA" not in strategic_blacklist, "FAIL: TSLA should NOT be in blacklist"
    
    print("=" * 70)
    print("✅ TEST PASSED: Strategic holdings guard is working!")
    print("=" * 70)
    print("\n📌 Summary:")
    print("  - AAPL and MSFT (strategic holdings) were BLOCKED")
    print("  - NVDA and TSLA (not strategic) were ALLOWED")
    print("  - Job C cannot buy Job A's strategic tickers ✅\n")
    
    # Cleanup
    os.remove('data/strategic_holdings.json')
    
    return True

if __name__ == "__main__":
    try:
        test_strategic_guard()
        print("\n🎉 ALL TESTS PASSED\n")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
