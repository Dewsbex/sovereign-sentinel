import sys
from trading212_client import Trading212Client
from audit_log import AuditLogger
import datetime

# Determine Job ID based on arguments
job_id = "SS004-PreFlight"
if "--postflight" in sys.argv:
    job_id = "SS009-PostFlight"

logger = AuditLogger(job_id)
logger.log("JOB_START", "System", f"Starting {job_id} check...")

try:
    client = Trading212Client()
    cash = client.get_account_summary()
    pos = client.get_open_positions()

    report = [
        f"*=== {job_id} STATUS ===*",
        f"Free Cash: £{cash.get('free', 0):,.2f}",
        f"Portfolio P/L: £{cash.get('ppl', 0):,.2f}\n",
        "*=== TOP POSITIONS ===*"
    ]

    if isinstance(pos, list):
        for p in pos[:10]:
            t = p.get('ticker') or p.get('instrument', {}).get('ticker', '???')
            t = t.replace('_US_EQ', '').replace('l_EQ', '')
            report.append(f"{t}: £{p.get('ppl', 0):>8.2f}")

    msg = "\n".join(report)
    client.send_telegram(msg)
    
    logger.log("JOB_COMPLETE", "System", "Check completed successfully", "SUCCESS")

except Exception as e:
    logger.log("JOB_ERROR", "System", str(e), "ERROR")
    print(f"Error: {e}")
