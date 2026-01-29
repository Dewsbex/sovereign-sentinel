import os
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load credentials
load_dotenv()
import config

def fetch_full_history():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 STARTING DEEP LEDGER SYNC...")
    
    # 1. AUTHENTICATION
    api_key = str(config.T212_API_KEY).strip()
    api_secret = str(config.T212_API_SECRET).strip() if config.T212_API_SECRET else None
    
    if not api_secret:
        print("❌ FAILED: API Secret missing. Cannot authenticate.")
        return

    from requests.auth import HTTPBasicAuth
    auth = HTTPBasicAuth(api_key, api_secret)
    
    headers = {
        "User-Agent": "SovereignSentinel/LedgerSync/1.0",
        "Content-Type": "application/json"
    }
    
    BASE_URL = "https://live.trading212.com/api/v0/"

    # 2. REQUEST EXPORT
    # We want EVERYTHING to reconstruct full history for "Time in Market"
    payload = {
        "dataIncluded": {
            "includeDividends": True,
            "includeInterest": True,
            "includeOrders": True,
            "includeTransactions": True
        },
        "timeFrom": "2020-01-01T00:00:00Z",
        "timeTo": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    print("   👉 Requesting CSV Report (Orders, Dividends, Interest)...")
    try:
        r_init = requests.post(f"{BASE_URL}equity/history/exports", json=payload, headers=headers, auth=auth)
        
        if r_init.status_code != 200:
            print(f"❌ ERROR: Failed to start export ({r_init.status_code})")
            print(r_init.text)
            return

        report_id = r_init.json().get('reportId')
        print(f"   ✅ Report Queued! ID: {report_id}")
        
        # 3. POLL FOR COMPLETION
        status = "Queued"
        download_link = None
        retries = 0
        
        while status not in ['Finished', 'Failed', 'Canceled'] and retries < 30:
            time.sleep(2) # Polling interval
            print(f"   ⏳ Checking status... ({retries+1})")
            
            r_check = requests.get(f"{BASE_URL}equity/history/exports", headers=headers, auth=auth)
            if r_check.status_code == 200:
                reports = r_check.json()
                # Find our report
                for rep in reports:
                    if rep.get('reportId') == report_id:
                        status = rep.get('status')
                        download_link = rep.get('downloadLink')
                        break
            
            retries += 1
        
        if status == 'Finished' and download_link:
            print(f"   🎉 Export Ready! Downloading...")
            r_file = requests.get(download_link)
            
            # Save to file
            filename = f"t212_ledger_{datetime.now().strftime('%Y%m%d')}.csv"
            with open(filename, 'wb') as f:
                f.write(r_file.content)
            
            print(f"   💾 SAVED: {filename} ({len(r_file.content)//1024} KB)")
            print("   ✅ This CSV contains the 'Truth' for 'Time-in-Market' calculations.")
            
        else:
            print(f"❌ Timed out or Failed. Status: {status}")

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    fetch_full_history()
