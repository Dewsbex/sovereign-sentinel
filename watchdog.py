import os
import sys
import requests
from trading212_client import Trading212Client

# CRITICAL SOVEREIGN FILES
# These must exist for the system to be considered "Battle Ready"
CRITICAL_FILES = [
    "main_bot.py",
    "trading212_client.py",
    "auditor.py",
    "monday_preflight.py"
]

def check_integrity():
    """Scans the directory for essential survival files."""
    missing = []
    for file in CRITICAL_FILES:
        if not os.path.exists(file):
            missing.append(file)
    return missing

def alert_human(missing_files):
    """
    Bypasses standard client to send emergency raw alert.
    If the client file itself is missing, we need a raw request fallback.
    """
    error_msg = (
        f"🚨 **CRITICAL FAILURE: WATCHDOG ALERT** 🚨\n\n"
        f"Job: `watchdog.py`\n"
        f"The following sovereign files are MISSING from the Oracle VPS:\n"
        f"`{', '.join(missing_files)}`\n\n"
        f"⚠️ AUTOMATED TRADING WILL FAIL AT 14:25 UTC."
    )

    try:
        # Try to use the unified client first
        client = Trading212Client()
        client.send_telegram(error_msg)
    except:
        # Fallback: Raw request if client is broken/missing
        token = os.getenv("TELEGRAM_TOKEN", "8585563319:AAH0wx3peZycxqG1KC9q7FMuSwBw2ps1TGA")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "7675773887")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={
            "chat_id": chat_id, 
            "text": error_msg,
            "parse_mode": "Markdown"
        })

if __name__ == "__main__":
    print("🐶 Watchdog: Starting pre-dawn integrity scan...")
    missing_items = check_integrity()
    
    if missing_items:
        print(f"❌ CRITICAL: Missing files: {missing_items}")
        alert_human(missing_items)
        sys.exit(1) # Exit with error to trigger cron failure log
    else:
        print("✅ Watchdog: All systems green. 07:55 UTC check passed.")
        sys.exit(0)
