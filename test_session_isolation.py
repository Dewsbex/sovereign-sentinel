"""
Portfolio Isolation Test - Session Manager Whitelist
Tests that check_risk_rules() ONLY processes positions from the session whitelist.
"""
import json
import os
import sys
from datetime import datetime

# Mock Trading212Client for testing
class MockTradingClient:
    def __init__(self, positions):
        self.mock_positions = positions
    
    def get_positions(self):
        return self.mock_positions

def test_session_isolation():
    """
    Test Scenario:
    - Strategic Holdings: AAPL, MSFT, GOOGL (NOT in session whitelist)
    - Session Positions: NVDA, TSLA (IN session whitelist)
    - All 5 tickers exist in targets.json
    
    Expected Result:
    - check_risk_rules() should ONLY return exits for NVDA, TSLA
    - AAPL, MSFT, GOOGL should be IGNORED (protected)
    """
    print("=" * 70)
    print("TEST: Session Manager Isolation")
    print("=" * 70)
    
    # Setup: Create mock session whitelist (only today's trades)
    session_whitelist = {
        "date": datetime.utcnow().strftime('%Y-%m-%d'),
        "tickers": ["NVDA", "TSLA"]
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/session_whitelist.json', 'w') as f:
        json.dump(session_whitelist, f, indent=2)
    
    # Setup: Create mock targets.json (all 5 tickers)
    targets = [
        {"ticker": "AAPL", "trigger_price": 150.0, "stop_loss": 145.0, "quantity": 10},
        {"ticker": "MSFT", "trigger_price": 300.0, "stop_loss": 290.0, "quantity": 5},
        {"ticker": "GOOGL", "trigger_price": 100.0, "stop_loss": 95.0, "quantity": 8},
        {"ticker": "NVDA", "trigger_price": 200.0, "stop_loss": 190.0, "quantity": 5},
        {"ticker": "TSLA", "trigger_price": 250.0, "stop_loss": 240.0, "quantity": 4}
    ]
    
    with open('data/targets.json', 'w') as f:
        json.dump(targets, f, indent=2)
    
    # Setup: Create mock broker positions (all 5 tickers held)
    mock_positions = [
        {"ticker": "AAPL", "quantity": 10, "averagePrice": 148.0, "currentPrice": 143.0},  # Below stop
        {"ticker": "MSFT", "quantity": 5, "averagePrice": 295.0, "currentPrice": 285.0},   # Below stop
        {"ticker": "GOOGL", "quantity": 8, "averagePrice": 98.0, "currentPrice": 93.0},    # Below stop
        {"ticker": "NVDA", "quantity": 5, "averagePrice": 195.0, "currentPrice": 188.0},   # Below stop
        {"ticker": "TSLA", "quantity": 4, "averagePrice": 245.0, "currentPrice": 238.0}    # Below stop
    ]
    
    # Import strategy engine
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from strategy_engine import SniperStrategy
    
    # Create strategy with mock client
    mock_client = MockTradingClient(mock_positions)
    strategy = SniperStrategy(mock_client)
    
    # Execute test
    print("\n📊 Mock Portfolio State:")
    print("  Strategic Holdings (NOT whitelisted): AAPL, MSFT, GOOGL")
    print("  Session Positions (whitelisted): NVDA, TSLA")
    print("  All 5 tickers are BELOW their stop-loss prices\n")
    
    exits = strategy.check_risk_rules()
    
    print(f"\n🔍 Risk Check Results: {len(exits)} exit signals generated\n")
    
    # Assertions
    exit_tickers = [e['ticker'] for e in exits]
    
    print("✅ EXPECTED: Only NVDA and TSLA should have exit signals")
    print(f"📋 ACTUAL: {exit_tickers}\n")
    
    # Test assertions
    assert len(exits) == 2, f"FAIL: Expected 2 exits, got {len(exits)}"
    assert "NVDA" in exit_tickers, "FAIL: NVDA should have exit signal"
    assert "TSLA" in exit_tickers, "FAIL: TSLA should have exit signal"
    assert "AAPL" not in exit_tickers, "FAIL: AAPL should be PROTECTED"
    assert "MSFT" not in exit_tickers, "FAIL: MSFT should be PROTECTED"
    assert "GOOGL" not in exit_tickers, "FAIL: GOOGL should be PROTECTED"
    
    print("=" * 70)
    print("✅ TEST PASSED: Session isolation is working correctly!")
    print("=" * 70)
    print("\n📌 Summary:")
    print("  - Strategic holdings (AAPL, MSFT, GOOGL) were IGNORED")
    print("  - Session positions (NVDA, TSLA) were PROCESSED")
    print("  - Job C cannot touch Job A's portfolio ✅\n")
    
    # Cleanup
    os.remove('data/session_whitelist.json')
    os.remove('data/targets.json')
    
    return True

if __name__ == "__main__":
    try:
        test_session_isolation()
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
