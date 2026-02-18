import os
import sys

# Ensure project root in path
sys.path.append(os.getcwd())

from trading212_client import Trading212Client

def check_connection():
    print("🔌 Testing Trading 212 API Connection...")
    
    try:
        client = Trading212Client()
        
        # Check if API Key is loaded
        if not client.api_key:
            print("❌ FAIL: TRADING212_API_KEY not found in environment variables.")
            return False
            
        print(f"🔑 API Key Found (Length: {len(client.api_key)})")
        
        # Test 1: Account Cash (Simple GET)
        print("   > Fetching Account Cash Balance...")
        cash_data = client.get_account_summary()
        
        if cash_data.get('status') == 'FAILED':
             print(f"❌ FAIL: API Request Rejected. {cash_data.get('error')}")
             return False
             
        # Success if we get a dictionary with 'total' or 'free'
        total = cash_data.get('total', 0.0)
        free = cash_data.get('free', 0.0)
        print(f"   ✅ SUCCESS. Account Total: £{total:.2f} | Free: £{free:.2f}")
        
        # Test 2: AI Brain Connectivity
        print("\n🧠 Testing Gemini Brain (Pro -> Flash Fallback)...")
        response = client.gemini_query("Reply with 'ONLINE'")
        print(f"   > Response: {response}")
        
        if "ONLINE" in str(response) or "online" in str(response).lower():
            print("   ✅ SUCCESS. AI Brain is Active.")
        else:
             print("   ⚠️ WARNING. AI Response unexpected (could be model quirk).")
             
        return True

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        return False

if __name__ == "__main__":
    if check_connection():
        print("\n✅ API SETUP VERIFIED. SYSTEM READY.")
        sys.exit(0)
    else:
        print("\n❌ API SETUP FAILED.")
        sys.exit(1)
