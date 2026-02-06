import os
import requests
import json
import time
from requests.auth import HTTPBasicAuth

# V32.40 - HISTORY EXPORT MODULE
print("🚀 TESTING HISTORY EXPORT...")

if __name__ == "__main__":
    t212_key = os.getenv('T212_API_KEY', '').strip()
    t212_secret = os.getenv('T212_API_SECRET', '').strip()
    auth = HTTPBasicAuth(t212_key, t212_secret)
    base_url = "https://live.trading212.com/api/v0/equity"
    
    # 1. Request a Report
    print("📡 Requesting new CSV verification report...")
    payload = {
        "reportType": "Orders",
        "timeFrom": "2024-01-01T00:00:00.000Z",
        "timeTo": "2025-01-01T00:00:00.000Z"
    }
    
    resp = requests.post(f"{base_url}/history/exports", json=payload, auth=auth, timeout=15)
    
    report_id = None
    if resp.status_code == 200:
        data = resp.json()
        report_id = data.get('reportId')
        print(f"✅ Report Requested! ID: {report_id}")
    else:
        print(f"❌ Failed to request report: {resp.text}")
        exit()

    # 2. Poll for Status
    if report_id:
        print("⏳ Polling for completion (Max 5 attempts)...")
        for i in range(5):
            time.sleep(2) # Wait 2s between checks
            r = requests.get(f"{base_url}/history/exports", auth=auth, timeout=15)
            if r.status_code == 200:
                reports = r.json()
                # Find our specific report
                target = next((item for item in reports if item["reportId"] == report_id), None)
                if target:
                    status = target.get('status')
                    print(f"   Attempt {i+1}: Status = {status}")
                    if status == "Finished":
                        print(f"✅ REPORT READY! Download URL: {target.get('downloadLink')}")
                        break
                else:
                    print(f"   Attempt {i+1}: Report ID not found in list yet...")
            else:
                print(f"⚠️ Polling failed: {r.status_code}")
