from trading212_client import Trading212Client
import sys

# Force utf-8 for windows console
sys.stdout.reconfigure(encoding='utf-8')

print("🧪 TESTING RESOLVE_TICKER...")
try:
    c = Trading212Client()
    
    tests = ['SOFI', 'RR.L', 'NVDA', 'TSLA', 'AAPL', 'VOD.L']
    
    for t in tests:
        ticker, meta = c.resolve_ticker(t)
        short = meta.get('shortName') if meta else "N/A"
        print(f"   {t} -> {ticker} (Short: {short})")
        
    print("✅ TEST COMPLETE")
except Exception as e:
    print(f"❌ TEST FAILED: {e}")
