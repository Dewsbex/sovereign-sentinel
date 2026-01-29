import os
import requests
import json
import time
import csv
import io
from datetime import datetime
from dotenv import load_dotenv

# Load credentials
load_dotenv()
try:
    import config
except ImportError:
    # Standalone support
    class Config:
        T212_API_KEY = os.getenv("T212_API_KEY")
        T212_API_SECRET = os.getenv("T212_API_SECRET")
    config = Config()

class LedgerSync:
    def __init__(self):
        self.api_key = str(config.T212_API_KEY).strip()
        self.api_secret = str(config.T212_API_SECRET).strip() if config.T212_API_SECRET else None
        
        self.base_url = "https://live.trading212.com/api/v0/"
        self.headers = {
            "User-Agent": "SovereignSentinel/LedgerSync/1.0",
            "Content-Type": "application/json"
        }
        
        if not self.api_secret:
             print("❌ LEDGER ERROR: API Secret missing. Cannot authenticate.")
             self.auth = None
        else:
             from requests.auth import HTTPBasicAuth
             self.auth = HTTPBasicAuth(self.api_key, self.api_secret)

        self.cache_file = "data/ledger_cache.json"
        
        if not os.path.exists("data"):
            os.makedirs("data")
            
        # User requested path for CSV storage
        self.drive_path = r"G:\My Drive\T212_ISA"
        if not os.path.exists(self.drive_path):
            print(f"   [WARN] Drive path not found: {self.drive_path}. Attempting create...")
            try:
                os.makedirs(self.drive_path, exist_ok=True)
                print(f"   [CREATED] Created directory: {self.drive_path}")
            except Exception as e:
                 print(f"   [ERROR] Failed to create drive path: {e}")
                 print("   [INFO] Falling back to local 'data' folder.")
                 self.drive_path = "data"
        else:
            print(f"   [CONFIG] CSV Export Target: {self.drive_path}")

    def run_sync(self, full_sync=False):
        """Orchestrates the sync process. Defaults to Delta (Current Year) unless full_sync=True."""
        if not self.auth:
            return False

        mode = "FULL (Multi-Year)" if full_sync else "DELTA (Current Year)"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] STARTING LEDGER SYNC [{mode}]...")
        
        # Test Write Permissions
        try:
            test_file = os.path.join(self.drive_path, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"   [CHECK] Write permissions OK for {self.drive_path}")
        except Exception as e:
            print(f"   [ERROR] Cannot write to {self.drive_path}: {e}")
            return False
            
        current_year = datetime.utcnow().year
        
        # Determine Years to Sync
        if full_sync:
            # Full History back to 2021
            start_year = 2021 
            years_to_sync = range(current_year, start_year - 1, -1)
            combined_data = {} # Reset data
        else:
            # Delta: Only Current Year
            years_to_sync = [current_year]
            # Load existing cache to merge into
            combined_data = self._load_existing_cache()
            print(f"   [LOAD] Loaded {len(combined_data)} existing assets from cache.")

        # Iterating
        for year in years_to_sync:
            print(f"-- Processing Year: {year} --")
            
            # Define Time Window
            t_start = f"{year}-01-01T00:00:00Z"
            if year == current_year:
                t_end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                t_end = f"{year}-12-31T23:59:59Z"
            
            # 1. Request Export
            download_url = self._request_export(t_start, t_end)
            if not download_url:
                continue
                
            # 2. Download CSV
            csv_content = self._download_csv(download_url)
            if not csv_content:
                continue
            
            # 3. Save Raw CSV (Backup)
            filename = f"T212_History_{year}.csv"
            save_path = os.path.join(self.drive_path, filename)
            try:
                with open(save_path, "wb") as f:
                    f.write(csv_content.encode('utf-8')) # Encode to bytes for 'wb' mode
                print(f"   [SAVE] Saved to {save_path}")
            except Exception as e:
                print(f"   [WARN] Failed to save CSV to drive: {e}")

            # 4. Parse & Merge into Cache
            chunk_data = self._analyze_csv(csv_content) # Keep original method name
            self._merge_data(combined_data, chunk_data)
            
            if full_sync:
                # Sleep to avoid rate limits between chunks only in full sync
                print("   [SLEEP] Cooling down for 20s...")
                time.sleep(20)
        
        # 5. Save Final Cache
        if combined_data:
            self._save_cache(combined_data)
            print("DTO LEDGER SYNC COMPLETE. Cached", len(combined_data), "assets.")
            return True
        else:
            print("DTO LEDGER SYNC FAILED or NO DATA.")
            return False

    def _merge_data(self, main_db, chunk_db):
        """Merges a yearly chunk into the main database."""
        for ticker, data in chunk_db.items():
            if ticker not in main_db:
                main_db[ticker] = data
            else:
                # 1. Update First Buy (Keep Earliest)
                if data['first_buy']:
                    current_first = main_db[ticker]['first_buy']
                    if not current_first or data['first_buy'] < current_first:
                         main_db[ticker]['first_buy'] = data['first_buy']
                
                # 2. Add Dividends
                main_db[ticker]['dividends'] += data['dividends']
                main_db[ticker]['buy_count'] += data['buy_count']

    def _request_export(self, t_start, t_end):
        """Requests CSV export for specific time range with Retry/Backoff."""
        payload = {
            "dataIncluded": {
                "includeDividends": True,
                "includeInterest": True,
                "includeOrders": True,
                "includeTransactions": True
            },
            "timeFrom": t_start,
            "timeTo": t_end
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                r = requests.post(f"{self.base_url}equity/history/exports", json=payload, headers=self.headers, auth=self.auth)
                
                # Check for Rate Limit (429 or BusinessException)
                if r.status_code == 429 or "TooManyRequests" in r.text:
                    wait_time = 60 * (attempt + 1) # Progressive backoff: 60s, 120s...
                    print(f"   [LIMIT] Rate limited. Waiting {wait_time}s before retry ({attempt+1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                
                if r.status_code != 200:
                    print(f"   [ERROR] API Error ({t_start[:4]}): {r.text}")
                    return None

                report_id = r.json().get('reportId')
                print(f"   [WAIT] Queued {t_start[:10]}... (ID: {report_id})", end="", flush=True)

                # Poll
                retries = 0
                while retries < 40: # 80 seconds max
                    time.sleep(2)
                    r_check = requests.get(f"{self.base_url}equity/history/exports", headers=self.headers, auth=self.auth)
                    if r_check.status_code == 200:
                        reports = r_check.json()
                        for rep in reports:
                            if rep.get('reportId') == report_id:
                                status = rep.get('status')
                                if status == 'Finished':
                                    print(" Done!")
                                    return rep.get('downloadLink')
                                elif status in ['Failed', 'Canceled']:
                                    print(f" Failed ({status})")
                                    return None
                    print(".", end="", flush=True)
                    retries += 1
                
                print(" Timeout.")
                return None

            except Exception as e:
                print(f"   [ERROR] Exception: {e}")
                return None
        
        print("   [FAIL] Max retries reached.")
        return None

    def _download_csv(self, url):
        try:
            print("   [DOWNLOAD] Downloading CSV...", end="")
            r = requests.get(url)
            print(f" OK ({len(r.content)//1024} KB)")
            return r.text
        except Exception as e:
            print(f" Error: {e}")
            return None

    def _analyze_csv(self, csv_text):
        """Parses CSV and calculates metrics per ticker."""
        data = {}
        reader = csv.DictReader(io.StringIO(csv_text))
        
        # We need to map weird tickers if necessary, but usually CSV matches API
        # T212 CSV Columns: Header, Action, Time, ISIN, Ticker, Name, No. of shares, Price / share, Total, ...
        
        for row in reader:
            ticker = row.get('Ticker')
            action = row.get('Action')
            date_str = row.get('Time')
            total_val = row.get('Total') # Amount involved
            
            if not ticker or not date_str:
                continue
                
            # Normalize Ticker (remove suffixes like .L or _US if needed for matching)
            # But the API usually returns full tickers. We'll store what we get.
            
            if ticker not in data:
                data[ticker] = {
                    'first_buy': None,
                    'dividends': 0.0, 
                    'buy_count': 0
                }
            
            # Parse Date (Format: 2024-01-25 14:30:00)
            try:
                row_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Handle potential millisecond format or different locale
                try: 
                    row_date = datetime.strptime(date_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                except:
                    continue

            # 1. Track First Buy Date
            if action in ['Market buy', 'Limit buy']:
                data[ticker]['buy_count'] += 1
                if data[ticker]['first_buy'] is None:
                    data[ticker]['first_buy'] = date_str
                else:
                    # Check if this row is earlier
                    current_first = datetime.strptime(data[ticker]['first_buy'], '%Y-%m-%d %H:%M:%S')
                    if row_date < current_first:
                         data[ticker]['first_buy'] = date_str

            # 2. Track Dividends
            if 'Dividend' in action:
                 try:
                     amt = float(str(total_val).replace('£','').replace('$',''))
                     data[ticker]['dividends'] += amt
                 except:
                     pass
        
        return data

    def _save_cache(self, data):
        meta = {
            "last_sync": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "assets": data
        }
        with open(self.cache_file, 'w') as f:
            json.dump(meta, f, indent=2)

    def _load_existing_cache(self):
        """Loads data from the existing ledger_cache.json if available."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    return cache.get('assets', {})
            except:
                pass
        return {}
            
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Force full multi-year sync")
    args = parser.parse_args()

    syncer = LedgerSync()
    syncer.run_sync(full_sync=args.full)
