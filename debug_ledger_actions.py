import requests
import json
import os
import csv
import io
import time
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class LedgerInspector:
    def __init__(self):
        self.api_key = os.environ.get("T212_API_KEY")
        self.api_secret = os.environ.get("T212_API_SECRET")
        self.base_url = "https://live.trading212.com/api/v0/"
        self.auth = HTTPBasicAuth(self.api_key, self.api_secret)
        self.headers = {"Content-Type": "application/json"}

    def run(self):
        print("[1] Requesting Export...")
        # Request all time history
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        payload = {
            "dataQueries": [
                {"data": "DIVIDENDS", "from": "2020-01-01T00:00:00Z"},
                {"data": "INTEREST", "from": "2020-01-01T00:00:00Z"},
                {"data": "ORDERS", "from": "2020-01-01T00:00:00Z"},
                {"data": "TRANSACTIONS", "from": "2020-01-01T00:00:00Z"}
            ],
            "format": "CSV"
        }
        
        r = requests.post(f"{self.base_url}equity/history/exports", json=payload, headers=self.headers, auth=self.auth)
        if r.status_code != 200:
            print(f"Error: {r.status_code} {r.text}")
            return
        
        report_id = r.json().get('reportId')
        print(f"Report ID: {report_id}")
        
        download_url = None
        for _ in range(30): # Wait 60s
            time.sleep(2)
            r_check = requests.get(f"{self.base_url}equity/history/exports", headers=self.headers, auth=self.auth)
            if r_check.status_code == 200:
                reports = r_check.json()
                for rep in reports:
                    if rep.get('reportId') == report_id:
                        status = rep.get('status')
                        if status == 'Finished':
                            download_url = rep.get('downloadLink')
                            break
                        elif status in ['Failed', 'Canceled']:
                            print(f"Export Failed: {status}")
                            return
            if download_url: break
            print(".", end="", flush=True)
            
        if not download_url:
            print("Timeout")
            return
            
        print("\n[2] Downloading CSV...")
        r_dl = requests.get(download_url)
        csv_text = r_dl.text
        
        print("[3] Analyzing Actions...")
        reader = csv.DictReader(io.StringIO(csv_text))
        action_totals = {}
        
        for row in reader:
            action = row.get('Action')
            total = row.get('Total')
            if not action or not total: continue
            
            try:
                amt = float(str(total).replace('£','').replace('$',''))
            except:
                continue
                
            if action not in action_totals:
                action_totals[action] = 0.0
            action_totals[action] += amt
            
        print("\n--- ACTION TOTALS ---")
        for action, total in sorted(action_totals.items(), key=lambda x: x[1], reverse=True):
            print(f"{action:30}: £{total:,.2f}")
            
        # Also sum specific categories
        positives = ['Dividend', 'Interest on cash', 'Securities lending income', 'Referral program bonus']
        negatives = ['FX fee', 'Tax', 'Stamp duty', 'Financing fee']
        
        total_p = sum(v for k,v in action_totals.items() if any(p in k for p in positives))
        total_n = sum(v for k,v in action_totals.items() if any(n in k for n in negatives))
        
        print("\n--- SUMMARY ---")
        print(f"Positive Non-Trade Income: £{total_p:,.2f}")
        print(f"Negative Non-Trade Fees:   £{total_n:,.2f}")
        print(f"Net Non-Trade:             £{total_p + total_n:,.2f}")

if __name__ == "__main__":
    inspector = LedgerInspector()
    inspector.run()
