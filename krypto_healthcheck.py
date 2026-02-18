#!/usr/bin/env python3
"""
Krypto Healthcheck: Daily Validation (8:05 AM EST)
Validates Kraken API, Redis, and Krypto infrastructure.
"""
import os
import sys
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8 for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from kraken_client import KrakenClient
    from telegram_bot import SovereignAlerts
except ImportError as e:
    print(f"Import error: {e}")
    print("Ensure kraken_client.py and telegram_bot.py are in the same directory")
    sys.exit(1)

def check_kraken_api():
    """Verify Kraken API connectivity and account status"""
    try:
        client = KrakenClient()
        balance = client.get_account_balance()
        if balance:
            # Calculate total USD value
            total_usd = sum(float(v) for k, v in balance.items() if k.endswith('USD'))
            return {
                "status": "✅ ONLINE", 
                "detail": f"Balance: ${total_usd:,.2f} | Assets: {len(balance)}"
            }
        return {"status": "⚠️ DEGRADED", "detail": "Unexpected response structure"}
    except Exception as e:
        return {"status": "❌ OFFLINE", "detail": str(e)}

def check_redis():
    """Verify Redis connection for message broker"""
    try:
        import redis
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            socket_timeout=5
        )
        r.ping()
        return {"status": "✅ CONNECTED", "detail": "Ping successful"}
    except Exception as e:
        return {"status": "❌ OFFLINE", "detail": str(e)}

def check_krypto_data():
    """Verify critical Krypto files and configuration"""
    krypto_dir = os.path.join(os.path.dirname(__file__), 'Krypto')
    
    if not os.path.exists(krypto_dir):
        return {"status": "❌ MISSING", "detail": "Krypto directory not found"}
    
    files = [
        'Krypto/requirements.txt',
        'Krypto/shared/broker.py',
        'Krypto/shared/schemas.py',
        'Krypto/manager/core.py'
    ]
    
    project_root = os.path.dirname(__file__)
    missing = [f for f in files if not os.path.exists(os.path.join(project_root, f))]
    
    if not missing:
        return {"status": "✅ COMPLETE", "detail": f"{len(files)} files verified"}
    return {"status": "⚠️ INCOMPLETE", "detail": f"Missing: {', '.join(missing)}"}

def run_krypto_healthcheck():
    """Execute full Krypto system healthcheck"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"KRYPTO HEALTHCHECK @ {timestamp}")
    
    # Run Checks
    api_check = check_kraken_api()
    redis_check = check_redis()
    data_check = check_krypto_data()
    
    # Build Report (Keep emojis for Telegram)
    report = f"""🔐 **KRYPTO HEALTHCHECK** ({timestamp})
Job: `krypto_healthcheck.py`

**Kraken API**: {api_check['status']}
  └ {api_check['detail']}

**Redis Broker**: {redis_check['status']}
  └ {redis_check['detail']}

**Data Integrity**: {data_check['status']}
  └ {data_check['detail']}

---
_Next check: Tomorrow 8:05 AM EST_
"""
    
    # Print status to console (Plain text for Windows safety)
    print(f"API: {api_check['status']} | Redis: {redis_check['status']} | Data: {data_check['status']}")
    
    # Send to Telegram (Krypto Channel)
    try:
        alerts = SovereignAlerts(use_krypto_channel=True)
        alerts.send_message(report)
        print("Report sent to Telegram (Krypto channel)")
    except Exception as e:
        print(f"Telegram send failed: {e}")
    
    # Log to file
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    with open(os.path.join(log_dir, "krypto_healthcheck.log"), "a", encoding='utf-8') as f:
        f.write(f"\n{timestamp} | API: {api_check['status']} | Redis: {redis_check['status']} | Data: {data_check['status']}\n")

if __name__ == "__main__":
    run_krypto_healthcheck()
