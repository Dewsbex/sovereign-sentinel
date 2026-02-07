"""
Test suite for Trading 212 API client
"""

from trading212_client import Trading212Client
import os

def test_authentication():
    """Test API authentication"""
    print("\n🔐 Testing Authentication...")
    try:
        client = Trading212Client()
        print("✅ Client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False


def test_get_positions():
    """Test fetching positions"""
    print("\n📊 Testing Position Retrieval...")
    try:
        client = Trading212Client()
        positions = client.get_positions()
        
        print(f"✅ Retrieved {len(positions)} positions")
        
        if positions:
            pos = positions[0]
            print(f"\nSample Position:")
            print(f"  Ticker: {pos.get('ticker')}")
            print(f"  Quantity: {pos.get('quantity')}")
            print(f"  P/L: {pos.get('ppl')}")
        
        return True
    except Exception as e:
        print(f"❌ Position retrieval failed: {e}")
        return False


def test_get_instrument():
    """Test fetching instrument metadata"""
    print("\n🔍 Testing Instrument Metadata...")
    try:
        client = Trading212Client()
        
        # Test with AAPL
        metadata = client.get_instrument_metadata('AAPL_US_EQ')
        
        print(f"✅ Retrieved metadata for AAPL_US_EQ")
        print(f"  Min Trade Quantity: {metadata.get('minTradeQuantity')}")
        print(f"  Currency: {metadata.get('currencyCode')}")
        print(f"  Type: {metadata.get('type')}")
        
        return True
    except Exception as e:
        print(f"❌ Metadata retrieval failed: {e}")
        return False


def test_max_buy_calculation():
    """Test max buy calculation"""
    print("\n💰 Testing Max Buy Calculation...")
    try:
        client = Trading212Client()
        
        # Simulate calculation with $1000 available cash
        max_qty = client.calculate_max_buy('AAPL_US_EQ', 1000.0, 175.50)
        
        print(f"✅ Max affordable shares: {max_qty}")
        print(f"  With $1000 @ $175.50/share")
        
        return True
    except Exception as e:
        print(f"❌ Max buy calculation failed: {e}")
        return False


def run_all_tests():
    """Run complete test suite"""
    print("=" * 50)
    print("TRADING 212 API - TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Authentication", test_authentication),
        ("Position Retrieval", test_get_positions),
        ("Instrument Metadata", test_get_instrument),
        ("Max Buy Calculation", test_max_buy_calculation)
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\n{total_passed}/{len(tests)} tests passed")
    
    return all(passed for _, passed in results)


if __name__ == '__main__':
    # Check for API key
    if not os.getenv('TRADING212_API_KEY'):
        print("❌ TRADING212_API_KEY environment variable not set")
        print("Set it using: export TRADING212_API_KEY='your_key_here'")
        exit(1)
    
    success = run_all_tests()
    exit(0 if success else 1)
