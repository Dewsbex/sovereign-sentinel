import json
from auditor import TradingAuditor

# 1. Verification of Iron Seed Logic (Safe)
print("🛡️ Test 1: Safe Exposure (< £1000)")
class SafeSim:
    def get_open_positions(self):
        # 300 + 300 + 300 = 900 (< 1000)
        return [{"value": 300}, {"value": 300}, {"value": 300}]

a = TradingAuditor()
a.client = SafeSim()
safe = a.enforce_iron_seed()
if safe:
    print("✅ Passed (Allowed)")
else:
    print("❌ Failed (Blocked Unexpectedly)")


# 2. Verification of Iron Seed Logic (Unsafe)
print("\n🛡️ Test 2: Unsafe Exposure (> £1000)")
class UnsafeSim:
    def get_open_positions(self):
        # 5 x 210 = 1050 (> 1000). All items are < 250 (Lab).
        return [
            {"value": 210}, {"value": 210}, {"value": 210}, 
            {"value": 210}, {"value": 210}
        ]

a.client = UnsafeSim()
unsafe = a.enforce_iron_seed()
if not unsafe:
    print("✅ Passed (Blocked Correctly)")
else:
    print("❌ Failed (Allowed Unexpectedly)")
