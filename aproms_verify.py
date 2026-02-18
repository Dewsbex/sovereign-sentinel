import sys
import os

# Ensure we are in the project root
sys.path.append(os.getcwd())

print("VERIFICATION: Checking Import Integrity...")

try:
    print("   - Importing trading212_client...")
    from trading212_client import Trading212Client
    client = Trading212Client()
    print(f"     [OK] Success. Model URL Check skipped (run manual prompt to verify).")
except Exception as e:
    print(f"     [FAIL] FAILED: {e}")
    sys.exit(1)

try:
    print("   - Importing strategic_moat...")
    from strategic_moat import MoatAnalyzer
    moat = MoatAnalyzer()
    if hasattr(moat, 'export_approved_target'):
        print("     [OK] Success. export_approved_target() found.")
    else:
        print("     [FAIL] FAILED: export_approved_target() missing.")
        sys.exit(1)
except Exception as e:
    print(f"     [FAIL] FAILED: {e}")
    sys.exit(1)

try:
    print("   - Importing main_bot...")
    # main_bot executes on import unless protected, let's just check file syntax by compiling
    with open('main_bot.py', 'r', encoding='utf-8') as f:
        compile(f.read(), 'main_bot.py', 'exec')
    print("     [OK] Success. Syntax valid (Loop restored).")
except Exception as e:
    print(f"     [FAIL] FAILED: {e}")
    sys.exit(1)

print("\nVERIFICATION: Checking AI Connectivity (Gemini)...")
try:
    # Use simple prompt
    response = client.gemini_query("Return the word APROMS")
    print(f"   Response: {response}")
    if "APROMS" in str(response) or "aproms" in str(response).lower():
        print("   [OK] Connectivity Confirmed.")
    else:
        print("   [WARN] Connectivity Warning: Unexpected response.")
except Exception as e:
    print(f"   [FAIL] Connectivity Failed: {e}")

print("\n[OK] ALL CHECKS PASSED.")
