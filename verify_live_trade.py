import os
import requests
import json
from requests.auth import HTTPBasicAuth

# V32.20 - THE AUTO-LINKER (Detection + Execution)
print("🚀 STARTING AUTO-LINKER TEST...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    
    if not t212_key:
        print("❌ ERROR: T212_API_KEY is empty.")
        exit(1)

    configs = [
        {"name": "LIVE v0 (Basic)", "url": "https://live.trading212.com/api/v0/equity", "auth": HTTPBasicAuth(t212_key, t212_secret), "headers": {}},
        {"name": "LIVE v1 (Header)", "url": "https://live.trading212.com/api/v1/equity", "auth": None, "headers": {"Authorization": t212_key}},
        {"name": "DEMO v0 (Basic)", "url": "https://demo.trading212.com/api/v0/equity", "auth": HTTPBasicAuth(t212_key, t212_secret), "headers": {}},
        {"name": "DEMO v1 (Header)", "url": "https://demo.trading212.com/api/v1/equity", "auth": None, "headers": {"Authorization": t212_key}}
    ]

    working_config = None
    for cfg in configs:
        print(f"📡 Checking {cfg['name']}...")
        try:
            r = requests.get(f"{cfg['url']}/account/cash", auth=cfg['auth'], headers=cfg['headers'], timeout=10)
            if r.status_code == 200:
                print(f"✅ FOUND WORKING CONFIG: {cfg['name']}")
                working_config = cfg
                break
        except:
            pass

    if not working_config:
        print("\n❌ VERDICT: All connection attempts failed with 401.")
        print("Please check your T212 API settings for IP Restriction (must be empty).")
        exit(1)

    # PLACE THE ORDER
    print(f"\n🚀 PROCEEDING TO PLACE ORDER ON {working_config['name']}...")
    trade_url = f"{working_config['url']}/orders/limit"
    
    ticker = "C" # Citigroup
    qty = 1.0
    price = 50.0 # Way below market, stays pending.
    
    payload = {
        "instrumentCode": f"{ticker}_US_EQ",
        "quantity": qty,
        "limitPrice": price,
        "timeValidity": "DAY"
    }
    
    print(f"📡 Sending 1.0 {ticker} @ ${price} Limit...")
    trade_resp = requests.post(trade_url, json=payload, auth=working_config['auth'], headers=working_config['headers'], timeout=10)
    
    print(f"📥 Trade Response Code: {trade_resp.status_code}")
    print(f"📄 Trade Response Body: {trade_resp.text}")
    
    if trade_resp.status_code == 200:
        print(f"\n✅ SUCCESS! Order is now PENDING in your {working_config['name']} account.")
        # Telegram Ping
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if token and chat_id:
            msg = f"🛰️ **V32.20 AUTO-LINK SUCCESS**\n\nVerified Link: {working_config['name']}\nPlaced 1.0 share of Citigroup (C) @ $50.00 Limit (Pending)."
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": msg})
    else:
        print("\n❌ ORDER FAILED but connection is working. Check instrument permissions.")
