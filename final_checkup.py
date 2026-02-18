import sys
import json
from trading212_client import Trading212Client
from auditor import TradingAuditor

def run_checkup():
    print("🏥 Running Final System Checkup (Neon Sentry)...")
    
    # 1. Sync Test
    client = Trading212Client()
    success = client.sync_master_list()
    if success:
        print("✅ Master List Sync: PASSED")
    else:
        print("❌ Master List Sync: FAILED")
        
    # 2. Master Validation Test (Check NVDA)
    nvda = client.validate_ticker("NVDA")
    if nvda:
        print(f"✅ Ticker Validation (NVDA): PASSED ({nvda.get('name', 'Unknown')})")
    else:
        print("❌ Ticker Validation (NVDA): FAILED")

    # 3. Iron Seed Test
    auditor = TradingAuditor()
    print("\n🛡️ Checking Iron Seed Protocol...")
    # This will print current exposure and status
    auditor.enforce_iron_seed()
    
    print("\n✅ Checkup Complete.")

if __name__ == "__main__":
    run_checkup()
