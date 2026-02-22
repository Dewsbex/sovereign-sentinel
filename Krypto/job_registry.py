#!/usr/bin/env python3
"""
Sovereign Sentinel: Job Registry (Single Source of Truth)
=========================================================
Canonical list of EVERY scheduled and persistent job across the system.
Run directly to print the full registry with audit status.
"""
import os
import sys
import csv
from datetime import datetime, timezone

# Force UTF-8
if hasattr(sys.stdout, 'buffer'):
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Legacy IDs for history lookup
LEGACY_AUDIT_IDS = {
    "SS009-MainBot": ["SS007-MainBot"],
    "SS005-PreFlight": ["SS004-PreFlight"],
    "SS010-PostFlight": ["SS009-PostFlight"],
    "SS006-ORBShield": ["SS014-ORBShield"],
    "SS007-MorningBrief": ["SS008-MorningBrief"],
    "SS008-ORBStrategy": ["SS015-ORBStrategy"],
    "SS011-DataSync": ["SS005-DataSync"],
    "SS002-Healthcheck": ["SS006-SystemCheck"],
}
# MASTER JOB LIST
# ---------------------------------------------------------------------------
# trigger_type: "CRON" = vps crontab, "SYSTEMD" = always-on service, "MANUAL" = ad-hoc
# audited: True = has AuditLogger JOB_START/JOB_COMPLETE, False = invisible
# audit_id: the process_name string used by AuditLogger (needed for log matching)

JOBS = [
    # ─── CRON JOBS (scheduled) ─────────────────────────────────────────────
    {
        "job_id": "SS001",
        "name": "Brain Update",
        "script": "athena_brain_updater.py",
        "trigger_type": "CRON",
        "trigger": "04:00 UTC daily",
        "platform": "SYSTEM",
        "audited": True,
        "audit_id": "SS001-BrainUpdate",
        "description": "Project Athena daily knowledge scan",
    },
    {
        "job_id": "SS002",
        "name": "Healthcheck",
        "script": "daily_heartbeat.py",
        "trigger_type": "CRON",
        "trigger": "13:00 UTC daily",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "SS002-Healthcheck",
        "description": "T212 API, data files, services validation",
    },
    {
        "job_id": "SS003",
        "name": "Krypto Health",
        "script": "krypto_healthcheck.py",
        "trigger_type": "CRON",
        "trigger": "13:05 UTC daily",
        "platform": "CRYPTO/KRAKEN",
        "audited": True,
        "audit_id": "SS003-KryptoHealth",
        "description": "Kraken API, Redis, E2E test validation",
    },
    {
        "job_id": "SS004",
        "name": "Watchdog",
        "script": "watchdog.py",
        "trigger_type": "CRON",
        "trigger": "07:55 UTC Mon-Fri",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "SS004-Watchdog",
        "description": "Pre-dawn integrity scan for critical files",
    },
    {
        "job_id": "SS005",
        "name": "PreFlight",
        "script": "monday_preflight.py",
        "trigger_type": "CRON",
        "trigger": "08:01 UTC Mon-Fri",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "SS005-PreFlight",
        "description": "London open: account, cash, positions check",
    },
    {
        "job_id": "SS006",
        "name": "ORB Shield",
        "script": "orb_shield.py",
        "trigger_type": "CRON",
        "trigger": "14:25 UTC Mon-Fri",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "SS006-ORBShield",
        "description": "Circuit breaker check before NYSE open",
    },
    {
        "job_id": "SS007",
        "name": "Morning Brief",
        "script": "strategic_moat.py",
        "args": "--brief",
        "trigger_type": "CRON",
        "trigger": "14:30 UTC Mon-Fri",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "SS007-MorningBrief",
        "description": "Strategy targets scan at NYSE open",
    },
    {
        "job_id": "SS008",
        "name": "ORB Strategy",
        "script": "orb_strategy.py",
        "trigger_type": "CRON",
        "trigger": "14:46 UTC Mon-Fri",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "SS008-ORBStrategy",
        "description": "15-min Opening Range Breakout analysis",
    },
    {
        "job_id": "SS009",
        "name": "Main Bot",
        "script": "main_bot.py",
        "args": "--live",
        "trigger_type": "CRON",
        "trigger": "14:25 UTC Mon-Fri",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "SS009-MainBot",
        "description": "Sniper engine: autonomous trade execution",
    },
    {
        "job_id": "SS010",
        "name": "PostFlight",
        "script": "monday_preflight.py",
        "args": "--postflight",
        "trigger_type": "CRON",
        "trigger": "21:30 UTC Mon-Fri",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "SS010-PostFlight",
        "description": "End-of-day P&L and positions summary",
    },
    {
        "job_id": "SS011",
        "name": "Data Sync",
        "script": "trading212_client.py",
        "args": "--sync",
        "trigger_type": "CRON",
        "trigger": "22:30 UTC daily",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "SS011-DataSync",
        "description": "Sync master_instruments.json from T212 API",
    },
    {
        "job_id": "SS012",
        "name": "Daily Diary",
        "script": r"C:\Users\steve\Author\daily_diary_job.py",
        "trigger_type": "CRON",
        "trigger": "22:00 UTC daily",
        "platform": "SYSTEM",
        "audited": True,
        "audit_id": "SS012-DailyDiary",
        "description": "Generate, Narrate, Publish (Telegram/Drive)",
    },

    # ─── SYSTEMD SERVICES (always-on) ─────────────────────────────────────
    {
        "job_id": "SVC01",
        "name": "Sovereign Bot",
        "script": "main_bot.py",
        "service_file": "sovereign-bot.service",
        "trigger_type": "SYSTEMD",
        "trigger": "Always-on (Restart=always)",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "SS009-MainBot",
        "description": "Live trading bot service (sovereign-bot.service)",
    },
    {
        "job_id": "SVC02",
        "name": "Telegram Control",
        "script": "telegram_listener.py",
        "service_file": "telegram-control.service",
        "trigger_type": "SYSTEMD",
        "trigger": "Always-on (Restart=always)",
        "platform": "SYSTEM",
        "audited": False,
        "audit_id": None,
        "description": "Telegram command listener (telegram-control.service)",
    },
    {
        "job_id": "SVC03",
        "name": "Athena Janitor",
        "script": "athena_janitor.py",
        "service_file": "athena_janitor.service",
        "trigger_type": "SYSTEMD",
        "trigger": "Always-on (Restart=always)",
        "platform": "SYSTEM",
        "audited": False,
        "audit_id": None,
        "description": "Google Drive sync/cleanup (athena_janitor.service)",
    },
    {
        "job_id": "SVC04",
        "name": "Sovereign Web",
        "script": "app.py",
        "service_file": "sovereign-web.service",
        "trigger_type": "SYSTEMD",
        "trigger": "Always-on (Restart=always)",
        "platform": "SYSTEM",
        "audited": False,
        "audit_id": None,
        "description": "Ghost UI dashboard via Gunicorn (sovereign-web.service)",
    },
    {
        "job_id": "SVC05",
        "name": "Alt Data Engine",
        "script": "alt_data_engine.py",
        "service_file": "alt_data_engine.service",
        "trigger_type": "SYSTEMD",
        "trigger": "Always-on (Restart=always)",
        "platform": "ISA/T212",
        "audited": False,
        "audit_id": None,
        "description": "Alternative data feed (alt_data_engine.service)",
    },
    {
        "job_id": "SVC06",
        "name": "Krypto Engine",
        "script": "AI_Brain/execution/engine.py",
        "service_file": "AI_Brain/infrastructure/systemd/krypto-engine.service",
        "trigger_type": "SYSTEMD",
        "trigger": "Always-on (Restart=always)",
        "platform": "CRYPTO/KRAKEN",
        "audited": False,
        "audit_id": None,
        "description": "Krypto trade execution engine (krypto-engine.service)",
    },
    {
        "job_id": "SVC07",
        "name": "Krypto Heartbeat",
        "script": "AI_Brain/remote/heartbeat.py",
        "service_file": "AI_Brain/infrastructure/systemd/krypto-heartbeat.service",
        "trigger_type": "SYSTEMD",
        "trigger": "Always-on (Restart=always)",
        "platform": "CRYPTO/KRAKEN",
        "audited": False,
        "audit_id": None,
        "description": "Krypto liveness heartbeat (krypto-heartbeat.service)",
    },
    {
        "job_id": "SVC08",
        "name": "Krypto Manager",
        "script": "Krypto/manager/core.py",
        "service_file": "Krypto/infra/systemd/krypto-manager.service",
        "trigger_type": "SYSTEMD",
        "trigger": "Always-on (Restart=always)",
        "platform": "CRYPTO/KRAKEN",
        "audited": False,
        "audit_id": None,
        "description": "Krypto execution manager (krypto-manager.service)",
    },

    # ─── MANUAL / AD-HOC SCRIPTS ──────────────────────────────────────────
    {
        "job_id": "AGT01",
        "name": "Krypto ORB",
        "script": "Krypto/agents/orb.py",
        "trigger_type": "AGENT",
        "trigger": "13:30 UTC (via SVC06)",
        "platform": "CRYPTO/KRAKEN",
        "audited": True,
        "audit_id": "AGT01-KryptoORB",
        "description": "BTC/ETH/SOL 15m Breakout Strategy",
    },
    {
        "job_id": "AGT02",
        "name": "Krypto Sentiment",
        "script": "Krypto/agents/sentiment.py",
        "trigger_type": "AGENT",
        "trigger": "Every 5m (via SVC06)",
        "platform": "CRYPTO/KRAKEN",
        "audited": True,
        "audit_id": "AGT02-KryptoSent",
        "description": "Alt Data: SOL/BONK/SHIB/PEPE/DOGE",
    },
    {
        "job_id": "MAN01",
        "name": "Force Brief",
        "script": "force_morning_brief.py",
        "trigger_type": "MANUAL",
        "trigger": "Ad-hoc (human triggered)",
        "platform": "ISA/T212",
        "audited": True,
        "audit_id": "Manual-Trigger",
        "description": "Force re-run of morning brief",
    },
]


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

AUDIT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "audit_log.csv")


def get_jobs(trigger_type=None, platform=None):
    """Filter jobs by trigger type and/or platform."""
    result = JOBS
    if trigger_type:
        result = [j for j in result if j["trigger_type"] == trigger_type]
    if platform:
        result = [j for j in result if j["platform"] == platform]
    return result


def get_job_by_id(job_id):
    """Look up a single job by its ID."""
    for j in JOBS:
        if j["job_id"] == job_id:
            return j
    return None


def get_expected_jobs_today():
    """Returns cron jobs that SHOULD run today based on day-of-week."""
    weekday = datetime.now(timezone.utc).weekday()  # 0=Mon, 6=Sun
    is_weekday = weekday < 5

    expected = []
    for j in JOBS:
        if j["trigger_type"] != "CRON":
            continue
        if "daily" in j["trigger"].lower():
            expected.append(j)
        elif "Mon-Fri" in j["trigger"] and is_weekday:
            expected.append(j)
    return expected


def _get_last_success_per_audit_id():
    """Scan audit log and return the last success-ish timestamp per process name."""
    last_ok = {}
    if not os.path.exists(AUDIT_FILE):
        return last_ok
    try:
        with open(AUDIT_FILE, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                process = row.get("Process", "")
                action = row.get("Action", "")
                status = row.get("Status", "")
                ts = row.get("Timestamp", "")
                # Count any of these as a "success" marker
                if status in ("SUCCESS", "HEARTBEAT") or action in (
                    "JOB_COMPLETE", "BRIEF_COMPLETE", "INIT_SUCCESS",
                    "HEARTBEAT_SENT", "BRIEF_SENT",
                ):
                    last_ok[process] = ts
    except Exception:
        pass
    return last_ok


def validate_scripts():
    """Check that all referenced script files exist on disk."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    missing = []
    for j in JOBS:
        if os.path.isabs(j["script"]):
             script_path = j["script"]
        else:
             script_path = os.path.join(base_dir, j["script"])
        if not os.path.exists(script_path):
            missing.append((j["job_id"], j["script"]))
    return missing


def print_registry():
    """Print the full job registry with audit status and last success."""
    now_utc = datetime.now(timezone.utc)
    day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][now_utc.weekday()]
    last_ok = _get_last_success_per_audit_id()

    print(f"\n{'='*115}")
    print(f"  SOVEREIGN SENTINEL - JOB REGISTRY ({day_name} {now_utc.strftime('%Y-%m-%d %H:%M UTC')})")
    print(f"{'='*115}")

    # HEADER
    # ID | Name | Type | Trigger | Audit | Last OK | Platform
    print(f"  {'ID':<7} {'Name':<18} {'Type':<8} {'Trigger':<28} {'Audit':<7} {'Last OK':<22} {'Platform'}")
    print(f"  {'-'*7} {'-'*18} {'-'*8} {'-'*28} {'-'*7} {'-'*22} {'-'*15}")

    # Unified list
    all_jobs = JOBS

    for j in all_jobs:
        audit_yn = "YES" if j["audited"] else "NO"
        last_ts = ""
        
        # Resolve Last OK (Checking current ID -> Legacy IDs)
        if j["audited"] and j["audit_id"]:
            # 1. Check current ID
            last_ts = last_ok.get(j["audit_id"])
            
            # 2. Check legacy IDs if not found
            if not last_ts and j["audit_id"] in LEGACY_AUDIT_IDS:
                for old_id in LEGACY_AUDIT_IDS[j["audit_id"]]:
                    found = last_ok.get(old_id)
                    if found:
                        last_ts = found # + " (Legacy)" # Optional: mark as legacy
                        break
            
            if not last_ts:
                last_ts = "Never"
        elif not j["audited"]:
            last_ts = "N/A"

        # Truncate trigger to fit column
        trigger_short = j["trigger"][:27]
        type_short = j["trigger_type"][:8]

        print(f"  {j['job_id']:<7} {j['name']:<18} {type_short:<8} {trigger_short:<28} {audit_yn:<7} {last_ts:<22} {j['platform']}")

    # Summary stats
    total = len(JOBS)
    audited = sum(1 for j in JOBS if j["audited"])
    unaudited = total - audited
    print(f"\n  Total: {total} jobs | Audited: {audited} | Unaudited: {unaudited}")

    # Validate scripts exist
    missing = validate_scripts()
    if missing:
        print(f"\n  WARNING: {len(missing)} scripts NOT FOUND on disk:")
        for job_id, script in missing:
            print(f"    {job_id}: {script}")
    else:
        print(f"  All scripts verified on disk.")
    print(f"{'='*115}\n")


if __name__ == "__main__":
    print_registry()
