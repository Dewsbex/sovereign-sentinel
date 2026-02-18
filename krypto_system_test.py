#!/usr/bin/env python3
"""
Krypto System Test: End-to-End Kraken Trading Stack Validation
Places and cancels a test crypto order to verify system functionality.
"""
import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8 for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from kraken_client import KrakenClient
from telegram_bot import SovereignAlerts

def run_krypto_system_test():
    print("🧪 STARTING KRYPTO E2E TEST (BTC)...")
    
    # 1. Initialize Components
    try:
        client = KrakenClient()
        alerts = SovereignAlerts(use_krypto_channel=True)
        print("✅ Components Initialized")
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return
    
    TEST_PAIR = "XXBTZUSD"  # BTC/USD
    TEST_VOLUME = 0.001      # 0.001 BTC (~$100 at current prices)
    
    # 2. Fetch Current Ticker
    print(f"📊 Fetching Ticker for {TEST_PAIR}...")
    try:
        ticker = client.get_ticker(TEST_PAIR)
        if not ticker:
            print(f"❌ Failed to fetch ticker for {TEST_PAIR}")
            return
        
        # Kraken ticker structure: {'a': [ask, ...], 'b': [bid, ...], 'c': [last, ...]}
        current_price = float(ticker['c'][0])  # Last trade price
        bid = float(ticker['b'][0])
        ask = float(ticker['a'][0])
        
        print(f"   Price: ${current_price:,.2f} | Bid: ${bid:,.2f} | Ask: ${ask:,.2f}")
        
    except Exception as e:
        print(f"❌ Ticker Fetch Failed: {e}")
        return
    
    # 3. Place Limit Order (5% below market to avoid execution)
    limit_price = round(current_price * 0.95, 2)
    print(f"🚀 Placing LIMIT BUY for {TEST_VOLUME} BTC @ ${limit_price:,.2f}...")
    
    try:
        order_response = client.place_limit_order(TEST_PAIR, TEST_VOLUME, limit_price, 'buy')
        
        if order_response and 'txid' in order_response:
            txids = order_response['txid']
            order_id = txids[0] if isinstance(txids, list) else txids
            print(f"✅ Order Placed! ID: {order_id}")
        else:
            print(f"❌ Order Placement Failed: {order_response}")
            return
            
    except Exception as e:
        error_str = str(e)
        if "Insufficient funds" in error_str:
            print(f"⚠️ Order Skipped: Insufficient Funds (API Keys Valid)")
            alerts.send_message(f"🧪 **KRYPTO TEST SKIPPED**\nInsufficient funds to place test order.\nAPI Connection: ✅ OK")
            return
        else:
            print(f"❌ Order Placement Error: {e}")
            return
    
    # 4. Send Telegram Alert
    try:
        test_msg = f"""🧪 **KRYPTO E2E TEST TRADE**
Pair: {TEST_PAIR}
Volume: {TEST_VOLUME} BTC
Type: LIMIT BUY @ ${limit_price:,.2f}
Status: PENDING CANCELLATION
Order ID: {order_id}"""
        alerts.send_message(test_msg)
        print("✅ Telegram Alert Sent")
    except Exception as e:
        print(f"⚠️ Telegram Alert Failed: {e}")
    
    # 5. Wait & Cancel
    print("⏳ Waiting 5 seconds before CANCEL...")
    time.sleep(5)
    
    try:
        print(f"🛑 Cancelling Order {order_id}...")
        cancel_result = client.cancel_order(order_id)
        print(f"   Cancel Result: {cancel_result}")
        
        completion_msg = f"""✅ **KRYPTO E2E TEST COMPLETE**
Order {order_id} Cancelled.
System Operational.
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        alerts.send_message(completion_msg)
        print("✅ Completion Alert Sent")
        
    except Exception as e:
        print(f"❌ Order Cancellation Failed: {e}")
        alerts.send_message(f"⚠️ **KRYPTO TEST WARNING**\nOrder {order_id} cancellation failed: {e}")
    
    print("\n🏁 TEST SEQUENCE FINISHED.")

if __name__ == "__main__":
    run_krypto_system_test()
