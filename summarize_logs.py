import csv
import sys
from collections import defaultdict

import datetime
log_file = sys.argv[1]
target_date = sys.argv[2] if len(sys.argv) > 2 else datetime.datetime.utcnow().strftime('%Y-%m-%d')

jobs_run = defaultdict(int)
errors = defaultdict(list)

try:
    with open(log_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        # Expected: Timestamp,Process,Action,Module,Details,Status
        for row in reader:
            if not row or len(row) < 6: continue
            ts, process, action, module, details, status = row[0], row[1], row[2], row[3], row[4], row[5]
            if ts.startswith(target_date):
                jobs_run[process] += 1
                if status == "ERROR" or "ERROR" in action:
                    errors[process].append(f"{action}: {details}")

    print(f"--- Jobs Run on {target_date} ---")
    for job, count in jobs_run.items():
        print(f"{job}: {count} log entries")
        if job in errors:
            print(f"  ERRORS: {len(errors[job])}")
            for err in set(errors[job]):
                print(f"    - {err}")
    if not jobs_run:
        print("No jobs found for that date.")
except Exception as e:
    print(f"Failed to parse log: {e}")
