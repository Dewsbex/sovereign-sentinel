import time
import subprocess
import sys
import os
from datetime import datetime, timezone

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
            
            if hour == 0 and ledger_run_today:
                ledger_run_today = False
                log("[RESET] Daily flags reset.")

            # --- MARKET HOURS LOGIC ---
            is_market_open = START_HOUR <= hour < END_HOUR
            
            if is_market_open:
                # Calculate time since last update
                time_since = time.time() - last_dashboard_update
                
                if time_since >= UPDATE_INTERVAL:
                    log(f"[UPDATE] MARKET OPEN. Updating Dashboard (Delta Sync)...")
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
                    log("[LEDGER] MARKET CLOSED. Initiating Daily Delta Sync...")
                    log("   (Backing up today's data to Google Drive)")
                    success = run_script("ledger_sync.py")
                    if success:
                        log("   [OK] Ledger Sync Complete.")
                    else:
                        log("   [FAIL] Ledger Sync Failed.")
                    ledger_run_today = True

            # Heartbeat (every 30s) updates the "Waiting" status line
            # But simple sleep is fine for now.
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n[STOP] Sentinel Daemon Stopped by User.")
            sys.exit(0)
        except Exception as e:
            log(f"[CRITICAL] DAEMON ERROR: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
