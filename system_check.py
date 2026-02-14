
import os
import sys
import time
import requests
import yfinance as yf
from datetime import datetime
from trading212_client import Trading212Client
from telegram_bot import SovereignAlerts

from audit_log import AuditLogger

def check_system():
    logger = AuditLogger("SS006-SystemCheck")
    logger.log("JOB_START", "System", "Starting Health Check")
    
    report = []
    errors = []
    
    print("🚦 SYSTEM CHECK INITIATED...")
    
    # 1. TIME CHECK (Critical for market open)
    now_utc = datetime.utcnow()
    report.append(f"🕒 **Time**: {now_utc.strftime('%H:%M:%S UTC')}")
    if now_utc.hour != 13 and sys.argv[1:] != ['--test']: # Expected run at 13:00 UTC
        # Warn but don't fail if running manually
        report.append(f"⚠️ **Time Warning**: Running outside 13:00 UTC schedule.")

    # 2. DISK/WRITE PERMISSIONS
    try:
        test_file = 'logs/write_test.tmp'
        os.makedirs('logs', exist_ok=True) # Ensure dir exists
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        report.append("✅ **Disk**: Write access confirmed.")
    except Exception as e:
        errors.append(f"❌ **Disk Error**: {e}")
        report.append(f"❌ **Disk**: FAILED ({e})")

    # 3. NETWORK CONNECTIVITY
    try:
        requests.get("https://www.google.com", timeout=5)
        report.append("✅ **Network**: Online.")
    except:
        errors.append("❌ **Network**: No internet connection.")
        report.append("❌ **Network**: FAILED.")

    # 4. DATA FEED (yfinance)
    try:
        ticker = yf.Ticker("SPY")
        hist = ticker.history(period="1d", interval="1m")
        if not hist.empty:
            last_price = hist['Close'].iloc[-1]
            report.append(f"✅ **Data**: Feed active (SPY: ${last_price:.2f}).")
        else:
            errors.append("❌ **Data**: SPY returned empty dataframe.")
            report.append("❌ **Data**: EMPTY RESPONSE.")
    except Exception as e:
        errors.append(f"❌ **Data Error**: {e}")
        report.append(f"❌ **Data**: FAILED ({e})")

    # 5. BROKER API (Trading212)
    try:
        client = Trading212Client()
        account = client.get_account_cash()
        if account:
            report.append(f"✅ **Broker**: API Connected (Cash: £{account.get('free', 0):.2f}).")
        else:
            errors.append("❌ **Broker**: Failed to fetch account cash.")
            report.append("❌ **Broker**: CONNECTION FAILED.")
    except Exception as e:
        errors.append(f"❌ **Broker Error**: {e}")
        report.append(f"❌ **Broker**: EXCEPTION ({e})")

    # --- FINAL VERDICT ---
    status = "✅ SYSTEM READY" if not errors else "❌ SYSTEM FAILURE"
    
    msg = f"{status}\n\n" + "\n".join(report)
    
    if errors:
        msg += "\n\n⚠️ **IMMEDIATE ATTENTION REQUIRED** ⚠️"
        logger.log("JOB_FAILURE", "System", "Checks Failed", "ERROR")
    else:
        logger.log("JOB_COMPLETE", "System", "All Systems Green", "SUCCESS")
        
    print(msg)
    
    # Send Telegram
    try:
        SovereignAlerts().send_message(msg)
    except Exception as e:
        print(f"FAILED TO SEND TELEGRAM: {e}")
        logger.log("ALERT_FAIL", "System", f"Telegram failed: {e}", "ERROR")

    # Return exit code for cron wrapper
    if errors:
        sys.exit(1)
    
if __name__ == "__main__":
    check_system()
