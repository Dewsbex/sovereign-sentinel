
import os
import sys
import shutil
import psutil
from datetime import datetime
from trading212_client import Trading212Client
from telegram_bot import SovereignAlerts

def run_preflight():
    print("🚀 STARTING PRE-FLIGHT CHECK...")
    
    # Init
    try:
        client = Trading212Client()
        alerts = SovereignAlerts()
    except Exception as e:
        print(f"❌ Init Failed: {e}")
        return

    report = []
    status = "GREEN"
    
    # 1. SYNC MASTER INSTRUMENTS (Job A Requirement)
    print("🔄 Syncing Master List...")
    try:
        success = client.sync_master_list()
        if success:
            report.append("✅ Instruments Synced")
            # Count them
            if os.path.exists('data/master_instruments.json'):
                size_mb = os.path.getsize('data/master_instruments.json') / (1024*1024)
                report.append(f"   (Data Size: {size_mb:.1f}MB)")
        else:
            report.append("❌ Instrument Sync FAILED")
            status = "RED"
    except Exception as e:
        report.append(f"❌ Sync Error: {e}")
        status = "RED"

    # 2. CHECK API CONNECTIVITY
    print("📶 Checking API...")
    try:
        acct = client.get_account_summary()
        if acct and 'total' in acct:
            cash = acct.get('free', 0)
            report.append(f"✅ API Connected (Free Cash: £{cash:.2f})")
        else:
            report.append(f"❌ API Connection FAILED: {acct}")
            status = "RED"
    except Exception as e:
        report.append(f"❌ API Error: {e}")
        status = "RED"

    # 3. SYSTEM HEALTH (VPS)
    print("💾 Checking System...")
    try:
        # Disk
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        if free_gb < 2:
            report.append(f"⚠️ LOW DISK SPACE: {free_gb}GB Free")
            status = "AMBER"
        else:
            report.append(f"✅ Disk OK ({free_gb}GB Free)")
            
        # Memory
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            report.append(f"⚠️ HIGH MEMORY: {mem.percent}% Used")
            status = "AMBER"
        else:
            report.append(f"✅ RAM OK ({mem.percent}% Used)")
            
    except Exception as e:
        report.append(f"⚠️ System Check Error: {e}")

    # 4. REPORT
    timestamp = datetime.utcnow().strftime('%H:%M OTC')
    emoji = "🟢" if status == "GREEN" else "🔴" if status == "RED" else "🟠"
    
    msg = f"{emoji} **PRE-FLIGHT: {status}**\nTime: {timestamp}\n\n" + "\n".join(report)
    
    print(msg)
    alerts.send_message(msg)
    
    if status == "RED":
        sys.exit(1)

if __name__ == "__main__":
    # Ensure data dir
    os.makedirs('data', exist_ok=True)
    run_preflight()
