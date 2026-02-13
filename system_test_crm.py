
import os
import sys
import time
import json
from datetime import datetime
from trading212_client import Trading212Client
from auditor import TradingAuditor
from telegram_bot import SovereignAlerts

def run_system_test():
    print("🧪 STARTING SOVEREIGN SENTINEL E2E TEST (CRM)...")
    
    # 1. Initialize Components
    try:
        client = Trading212Client()
        auditor = TradingAuditor()
        alerts = SovereignAlerts()
        print("✅ Components Initialized")
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    TEST_TICKER = "CRM"
    TEST_QTY = 0.1
    
    # 2. Data Fetch & Auditor Check
    print(f"📊 Fetching Data for {TEST_TICKER}...")
    import yfinance as yf
    try:
        t = yf.Ticker(TEST_TICKER)
        info = t.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('last_price', 0)))
        bid = info.get('bid', 0)
        ask = info.get('ask', 0)
        avg_vol = info.get('averageVolume', 0)
        
        print(f"   Price: ${current_price:.2f} | Bid: ${bid:.2f} | Ask: ${ask:.2f} | Vol: {avg_vol:,}")
        
        # Test Auditor (Should PASS normally for CRM)
        print("🛡️ Testing Auditor Checks...")
        if not auditor.check_volume_filter(TEST_TICKER, avg_vol):
            print("❌ Volume Filter REJECTED (Unexpected for CRM)")
        else:
            print("✅ Volume Filter PASSED")
            
        if not auditor.check_spread_guard(TEST_TICKER, bid, ask):
             print("❌ Spread Guard REJECTED")
        else:
             print("✅ Spread Guard PASSED")
             
    except Exception as e:
        print(f"❌ Data Fetch Failed: {e}")
        return

    # 3. Execution (Safe Limit Order)
    limit_price = round(current_price * 0.99, 2) # 1% Below Market
    print(f"🚀 Placing LIMIT BUY for {TEST_QTY} {TEST_TICKER} @ ${limit_price}...")
    
    order_response = client.place_limit_order(TEST_TICKER, TEST_QTY, limit_price, "BUY")
    
    order_id = None
    if order_response and 'id' in order_response: # T212 returns dictionary with 'id' usually, or check response structure
        # The client wrapper returns .json()
        print(f"✅ Order Placed! Response: {order_response}")
        order_id = order_response.get('id')
    else:
        # Check if it's a list (some endpoints) or error
        print(f"❌ Order Placement Failed: {order_response}")
        return

    # 4. Telegram Alert
    alerts.send_message(f"🧪 **E2E TEST TRADE**\nTicker: {TEST_TICKER}\nQty: {TEST_QTY}\nType: LIMIT BUY @ ${limit_price}\nStatus: PENDING CANCELLATION")
    print("✅ Telegram Alert Sent")

    # 5. Wait & Cancel
    print("⏳ Waiting 5 seconds before CANCEL...")
    time.sleep(5)
    
    if order_id:
        print(f"🛑 Cancelling Order {order_id}...")
        cancel_res = client.cancel_order(order_id)
        print(f"   Cancel Result: {cancel_res}")
        alerts.send_message(f"✅ **E2E TEST COMPLETE**\nOrder {order_id} Cancelled.\nSystem Operational.")
    
    print("\n🏁 TEST SEQUENCE FINISHED.")

if __name__ == "__main__":
    run_system_test()
