import os
import sys
import logging
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY")

print("--- SHADOW PROTOCOL DIAGNOSTIC ---")

# 1. Environment Check
token = os.getenv('TELEGRAM_TOKEN', '')
chat_id = os.getenv('TELEGRAM_CHAT_ID', '')

print(f"ENV: TELEGRAM_TOKEN Length: {len(token)}")
print(f"ENV: TELEGRAM_CHAT_ID Length: {len(chat_id)}")

if not token or not chat_id:
    print("❌ Critical: Missing Telegram Credentials in Environment")
else:
    print("✅ Credentials Present")

# 2. Raw Connectivity execution
print("\n--- 2. Testing Raw Connectivity ---")
if token and chat_id:
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': "🔍 Shadow Protocol Connection Test (Raw Request)",
            'parse_mode': 'HTML'
        }
        resp = requests.post(url, json=payload, timeout=10)
        print(f"Raw Response: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"❌ Raw Request Failed: {e}")

# 3. Bot Logic Test
print("\n--- 3. Testing Bot Logic ---")
try:
    from main_bot import Strategy_ORB
    bot = Strategy_ORB()
    
    ticker = "SHA_DOW"
    qty = 50
    trigger_price = 150.00
    stop_loss = 145.00

    print(f"Simulating Shadow Exec for {ticker}...")
    success, fill = bot.execute_trade(ticker, "BUY", qty, trigger_price, stop_loss)
    
    if success:
        print("✅ Bot Execute Method Returned Success")
    else:
        print("❌ Bot Execute Method Failed")
        
except Exception as e:
    print(f"❌ Bot Initialization/Execution Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n--- DIAGNOSTIC COMPLETE ---")
