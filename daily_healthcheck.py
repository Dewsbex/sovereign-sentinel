#!/usr/bin/env python3
"""
Sovereign Sentinel: Daily Healthcheck (8:00 AM)
Validates all critical components and sends Telegram report.
"""
import os
import sys
import json
from datetime import datetime
from trading212_client import Trading212Client
from telegram_bot import SovereignAlerts

def check_trading_api():
    """Verify Trading212 API connectivity"""
    try:
        client = Trading212Client()
        account = client.get_account_info()
        if account and 'cash' in account:
            return {"status": "✅ ONLINE", "detail": f"Cash: £{account['cash']:,.2f}"}
        return {"status": "⚠️ DEGRADED", "detail": "Unexpected response structure"}
    except Exception as e:
        return {"status": "❌ OFFLINE", "detail": str(e)}

def check_data_files():
    """Verify critical data files exist"""
    files = [
        'data/master_instruments.json',
        'data/audit_trades.csv',
        'config.json'
    ]
    missing = [f for f in files if not os.path.exists(f)]
    if not missing:
        return {"status": "✅ COMPLETE", "detail": f"{len(files)} files verified"}
    return {"status": "⚠️ INCOMPLETE", "detail": f"Missing: {', '.join(missing)}"}

def check_services():
    """Verify systemd services via subprocess"""
    import subprocess
    services = ['sovereign-bot', 'athena_janitor', 'telegram-control', 'sovereign-web']
    results = {}
    for svc in services:
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', svc],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_active = result.stdout.strip() == 'active'
            results[svc] = "✅" if is_active else "❌"
        except Exception as e:
            results[svc] = "⚠️"
    
    active_count = sum(1 for v in results.values() if v == "✅")
    return {
        "status": "✅ OPERATIONAL" if active_count == len(services) else "⚠️ DEGRADED",
        "detail": " | ".join([f"{k}: {v}" for k, v in results.items()])
    }

def run_healthcheck():
    """Execute full system healthcheck"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"🏥 HEALTHCHECK @ {timestamp}")
    
    # Run Checks
    api_check = check_trading_api()
    data_check = check_data_files()
    service_check = check_services()
    
    # Build Report
    report = f"""🏥 **DAILY HEALTHCHECK** ({timestamp})
Job: `daily_healthcheck.py`

**Trading API**: {api_check['status']}
  └ {api_check['detail']}

**Data Integrity**: {data_check['status']}
  └ {data_check['detail']}

**System Services**: {service_check['status']}
  └ {service_check['detail']}

---
_Next check: Tomorrow 8:00 AM EST_
"""
    
    print(report)
    
    # Send to Telegram
    try:
        alerts = SovereignAlerts()
        alerts.send_message(report)
        print("✅ Report sent to Telegram")
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")
    
    # Log to file
    with open("logs/healthcheck.log", "a") as f:
        f.write(f"\n{timestamp} | API: {api_check['status']} | Data: {data_check['status']} | Services: {service_check['status']}\n")

if __name__ == "__main__":
    run_healthcheck()
