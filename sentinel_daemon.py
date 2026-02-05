import time
import subprocess
import sys
import os
import json
from datetime import datetime, timezone

def ensure_ledger_exists():
    """Ensures the ledger directory and file exist with valid structure."""
    path = "data/ledger_cache.json"
    os.makedirs("data", exist_ok=True)
    if not os.path.isfile(path):
        with open(path, "w") as f:
            json.dump({}, f)
        print(f"Initialized new ledger: {path}")

# --- CONFIGURATION ---
START_HOUR = 9   # 09:00 GMT
END_HOUR = 21    # 21:00 GMT
UPDATE_INTERVAL = 300  # 5 Minutes (in seconds)
LEDGER_SYNC_HOUR = 21  # Run once, immediately after close

def log(msg):
    timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
    print(f"[{timestamp} GMT] {msg}")

def run_script(script_name):
    """Runs a python script as a subprocess."""
    try:
        # Use sys.executable to ensure we use the same python interpreter
        # Timeout added to prevent infinite hanging
        subprocess.run([sys.executable, script_name], check=True, timeout=120)
        return True
    except subprocess.TimeoutExpired:
        log(f"   [ERROR] {script_name} timed out (>120s).")
        return False
    except subprocess.CalledProcessError as e:
        log(f"   [ERROR] {script_name} failed: {e}")
        return False
    except Exception as e:
        log(f"   [ERROR] Could not start {script_name}: {e}")
        return False

def broadcast_update():
    """Commits and pushes the updated index.html to GitHub/Cloudflare."""
    try:
        # Add only the dashboard file
        subprocess.run(["git", "add", "index.html"], check=True, stdout=subprocess.DEVNULL, timeout=10)
        
        # Commit with timestamp
        timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
        commit_msg = f"Auto-Update: Price Delta Sync [{timestamp} GMT]"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, stdout=subprocess.DEVNULL, timeout=10)
        
        # Push to remote (Timeout important here)
        subprocess.run(["git", "push"], check=True, stdout=subprocess.DEVNULL, timeout=30)
        return True
    except subprocess.TimeoutExpired:
        log(f"   [WARN] Git timed out. (Check if authentication is needed).")
        return False
    except subprocess.CalledProcessError as e:
        # It's okay if commit fails (e.g. no changes)
        log(f"   [INFO] Broadcast skipped (No changes or Git Error).")
        return False

def main():
    # Ensure ledger exists before starting the sentinel loop
    ensure_ledger_exists()
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*60)
    print("      SOVEREIGN SENTINEL AUTONOMOUS NODE")
    print(f"      Active Window: {START_HOUR}:00 - {END_HOUR}:00 GMT")
    print("      Broadcast Mode: ACTIVE (Pushing to Cloudflare)")
    print("="*60)
    
    last_dashboard_update = 0
    ledger_run_today = False
    
    # Main Loop
    while True:
        try:
            now = datetime.now(timezone.utc)
            hour = now.hour
            
            # --- ORB BOT AUTOMATION (14:15 - 21:30 GMT) ---
            # Launch the trading bot automatically
            ORB_START = 14
            ORB_MINUTE = 15
            ORB_END = 21
            ORB_END_MINUTE = 30
            
            # Simple check: Is it trading time?
            orb_active_window = False
            if hour > ORB_START or (hour == ORB_START and now.minute >= ORB_MINUTE):
                if hour < ORB_END or (hour == ORB_END and now.minute < ORB_END_MINUTE):
                    orb_active_window = True
            
            if orb_active_window:
                # Check if running
                # Note: This is a simple check. In production, we might use PID files.
                # Here we just rely on Popen not blocking. 
                # Ideally we check if process is alive, but for now let's just launch it if we haven't tracked it?
                # A robust way is to check tasklist.
                
                # We will use a flag 'bot_launched_today' relative to the window.
                # But if the daemon restarts, it loses the flag.
                # Let's check process list using tasklist for 'main_bot.py' (this is tricky in python since it shows as python.exe)
                # For this user environment, let's trust a simple logic:
                # If we are in the window and haven't launched it "in this daemon session", try to launch?
                # Better: Check if a specific lock file or just assume the user runs this daemon once.
                
                # Let's use a specialized function to check if main_bot is running
                pass # Logic implemented below

            # --- MARKET HOURS LOGIC ---
            is_market_open = START_HOUR <= hour < END_HOUR
            
            if is_market_open:
                # 0. ORB BOT CHECK (Process Manager)
                if orb_active_window:
                    # Check if main_bot.py is running
                    try:
                        # tasklist /FI "IMAGENAME eq python.exe" /V
                        # checking command line args is harder in pure windows cmd without wmic
                        # Let's use a marker file? Or just launch it?
                        # Let's just launch it and let main_bot handle single-instance locking if possible?
                        # main_bot doesn't have locking.
                        
                        # Let's use wmic to check command line
                        check_cmd = 'wmic process where "name=\'python.exe\'" get commandline'
                        proc_list = subprocess.run(check_cmd, capture_output=True, text=True, shell=True).stdout
                        
                        if "main_bot.py" not in proc_list:
                            log("[ORB] Bot not running. Launching main_bot.py...")
                            # Launch detached
                            subprocess.Popen([sys.executable, "main_bot.py"], 
                                             creationflags=subprocess.CREATE_NEW_CONSOLE)
                            log("[ORB] Bot launched in new window.")
                        else:
                            # log("   [ORB] Bot is running.")
                            pass
                    except Exception as e:
                        log(f"   [WARN] Could not check/launch bot: {e}")

                # Calculate time since last update
                time_since = time.time() - last_dashboard_update
                
                if time_since >= UPDATE_INTERVAL:
                    log(f"[UPDATE] MARKET OPEN. Updating Dashboard + Portfolio CSV...")
                    
                    # 1. Generate ISA Portfolio CSV (Source of Truth)
                    log("   [CSV] Generating ISA_PORTFOLIO.csv...")
                    csv_success = run_script("generate_isa_portfolio.py")
                    if csv_success:
                        log("   [CSV] Portfolio CSV Updated.")
                    else:
                        log("   [WARN] CSV generation failed, continuing with dashboard...")
                    
                    # 2. Update Dashboard
                    success = run_script("generate_static.py")
                    if success:
                        log("   [OK] Update Complete. Broadcasting to Live Site...")
                        if broadcast_update():
                            log("   [LIVE] Dashboard Published to Web.")
                        last_dashboard_update = time.time()
                    else:
                        log("   [FAIL] Update Failed.")
                
            # --- LEDGER SYNC LOGIC (AFTER CLOSE) ---
            # Run once when hour hits LEDGER_SYNC_HOUR (21:00)
            elif hour == LEDGER_SYNC_HOUR:
                if not ledger_run_today:
                    log("[LEDGER] MARKET CLOSED. Initiating Daily Ledger Sync...")
                    log("   (This backs up full history to Google Drive)")
                    success = run_script("ledger_sync.py")
                    if success:
                        log("   [OK] Ledger Sync Complete.")
                    else:
                        log("   [FAIL] Ledger Sync Failed.")
                    ledger_run_today = True

            # Heartbeat (every 30s) updates the "Waiting" status line
            # But simple sleep is fine for now.
            time.sleep(30)
            
            # Run every 5 minutes (CHECK REMOVED - we need faster loop for ORB check)
            # The loop is controlled by time.sleep(30) at the bottom.
            # We removed the extra sleep(300) to allow responsive process checking.
            
        except KeyboardInterrupt:
            print("\n[STOP] Sentinel Daemon Stopped by User.")
            sys.exit(0)
        except Exception as e:
            log(f"[CRITICAL] DAEMON ERROR: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
