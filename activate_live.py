import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.25 - FINAL LIVE ACTIVATION TEST
print("🚀 STARTING FINAL ACTIVATION TEST...")
print("NOTE: If you get a 429 error, please wait 5 minutes and try again.")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    
    auth = HTTPBasicAuth(t212_key, t212_secret)
    # Using the EXACT format verified in the forensic test
    ticker = "NUE"
    instrument_code = f"{ticker}_US_EQ"
    
    # Place a safe limit order (1 share @ $100)
    # This will sit in "Pending Orders" and not execute tonight.
    url = "https://live.trading212.com/api/v0/equity/orders/limit"
    payload = {
        "instrumentCode": instrument_code,
        "quantity": 1.0,
        "limitPrice": 100.0,
        "timeValidity": "DAY"
    }

    print(f"📡 Sending 1 share {ticker} limit order to T212...")
    try:
        resp = requests.post(url, json=payload, auth=auth, timeout=10)
        print(f"📥 Response Code: {resp.status_code}")
        print(f"📄 Response Body: {resp.text}")
        
        if resp.status_code == 200:
            print("\n✅ SUCCESS! The trade is PENDING in your T212 account.")
            print("🚀 LIVE TRADING IS NOW ARMED AND READY.")
            
            # Final Telegram Confirmation
            token = os.getenv('TELEGRAM_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            if token and chat_id:
                msg = "🔔 **LIVE TRADING ACTIVATED**\n\nVerification successful. T212 credentials verified. End-to-end trade routing confirmed."
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": msg})
        else:
            print(f"\n❌ FAILED ({resp.status_code}).")
            if resp.status_code == 429:
                print("REASON: Rate limited. Please wait 5 minutes.")
    except Exception as e:
        print(f"❌ ERROR: {e}")
