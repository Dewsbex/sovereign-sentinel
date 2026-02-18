import sys
import json
from trading212_client import Trading212Client
from auditor import TradingAuditor

# MOCK CLASS
class MockClient(Trading212Client):
    def get_open_positions(self):
        print("🧪 [MOCK] Returning Portfolio: 5x 'Seed' trades (£50 each) + 1x Main Holding (£5000)")
        return [
            {"ticker": "LAB1", "value": 50.0, "quantity": 1},
            {"ticker": "LAB2", "value": 50.0, "quantity": 1},
            {"ticker": "LAB3", "value": 50.0, "quantity": 1},
            {"ticker": "LAB4", "value": 50.0, "quantity": 1}, 
            {"ticker": "LAB5", "value": 50.0, "quantity": 1}, # Total Lab = £250
            {"ticker": "MAIN", "value": 5000.0, "quantity": 10} # Ignored by auditor (>250)
        ]

def run_mock_checkup():
    print("🏥 Running Final System Checkup (OFFLINE/MOCK MODE)...")
    
    # 1. Master List Check (using file created)
    client = Trading212Client()
    # Mocking validate_ticker requires data/master_instruments.json (which I created in prev step)
    
    try:
        nvda = client.validate_ticker("NVDA")
        if nvda:
            print(f"✅ Ticker Validation (NVDA): PASSED ({nvda.get('name')})")
        else:
            print("❌ Ticker Validation (NVDA): FAILED")
    except Exception as e:
        print(f"⚠️ Validation Error: {e}")

    # 2. Iron Seed Test (Safe Scenario)
    auditor = TradingAuditor()
    print("\n🛡️ Testing Iron Seed Protocol (Safe Scenario)...")
    
    # Inject Mock Client
    auditor.client = MockClient() 
    
    # Should be £250 exposure -> Safe
    is_safe = auditor.enforce_iron_seed()
    
    if is_safe:
        print("✅ Iron Seed Logic: PASSED (Under Limit)")
    else:
        print("❌ Iron Seed Logic: FAILED (False Positive)")
        
    # 3. Iron Seed Test (Unsafe Scenario)
    print("\n🛡️ Testing Iron Seed Protocol (Unsafe Scenario)...")
    
    # Create an unsafe Mock Client on the fly
    class UnsafeMockClient:
        def get_open_positions(self):
            return [{"ticker": "BIG_LAB", "value": 1500.0}] # > £1000, but is it < 250? No.
            # Wait, logic is: sum positions < 250.
            # If position is 1500, it is IGNORED by the filter, so exposure is 0.
            # Ah! To test the LIMIT, we need MANY small positions that sum > 1000.
            
    # Correct Unsafe Scenario: Imagine 5 trades of £210 each = £1050 total exposure
    class DangerousMockClient:
        def get_open_positions(self):
            return [
                {"ticker": "D1", "value": 210.0},
                {"ticker": "D2", "value": 210.0},
                {"ticker": "D3", "value": 210.0},
                {"ticker": "D4", "value": 210.0},
                {"ticker": "D5", "value": 210.0}
            ]

    auditor.client = DangerousMockClient()
    is_safe_fail = auditor.enforce_iron_seed()
    
    if not is_safe_fail:
         print("✅ Iron Seed Logic: PASSED (Correctly Blocked)")
    else:
         print("❌ Iron Seed Logic: FAILED (False Negative - Limit Breach Allowed)")


if __name__ == "__main__":
    run_mock_checkup()
