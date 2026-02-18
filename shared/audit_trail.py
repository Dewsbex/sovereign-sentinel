"""
Centralized Audit Trail — Unified event logging for the Antigravity ecosystem.
Replaces per-project CSV/log files with a single SQLite database.
Drop-in compatible with existing AuditLogger interface.
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "audit_trail.db"

def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    """Create audit_events table if it doesn't exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            project TEXT NOT NULL,
            event_type TEXT,
            severity TEXT DEFAULT 'INFO',
            target TEXT DEFAULT '-',
            details TEXT,
            user_notified INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_audit_project ON audit_events(project);
        CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_events(severity);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);
    """)
    conn.commit()
    conn.close()

# Ensure DB exists on import
init_db()


class CentralAuditLogger:
    """
    Drop-in replacement for per-project AuditLogger.
    Same interface: .log(action, target, details, status)
    Writes to the centralized SQLite audit trail.
    """

    STATUS_ICONS = {
        "INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️",
        "ERROR": "❌", "CRITICAL": "🔥", "HEARTBEAT": "💓"
    }

    def __init__(self, project_name="orchestrator"):
        self.project = project_name

    def log(self, action, target="-", details="", status="INFO"):
        """Log an event to the centralized audit trail."""
        timestamp = datetime.utcnow().isoformat()

        # Console output
        icon = self.STATUS_ICONS.get(status.upper(), "📝")
        if status.upper() != "HEARTBEAT":
            print(f"{icon} [{timestamp}] {self.project} | {action}: {target} - {details}")

        # SQLite write
        try:
            conn = get_connection()
            conn.execute("""
                INSERT INTO audit_events (timestamp, project, event_type, severity, target, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, self.project, action, status.upper(), target, details))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Audit write failed: {e}")


# --- Query Functions ---

def get_events(project=None, severity=None, since_hours=None, limit=100):
    """Query audit events with optional filters."""
    conn = get_connection()
    query = "SELECT * FROM audit_events WHERE 1=1"
    params = []

    if project:
        query += " AND project = ?"
        params.append(project)
    if severity:
        query += " AND severity = ?"
        params.append(severity.upper())
    if since_hours:
        cutoff = (datetime.utcnow() - timedelta(hours=since_hours)).isoformat()
        query += " AND timestamp >= ?"
        params.append(cutoff)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_recent_errors(hours=24):
    """Get errors and criticals from the last N hours."""
    conn = get_connection()
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    rows = conn.execute("""
        SELECT * FROM audit_events
        WHERE severity IN ('ERROR', 'CRITICAL') AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (cutoff,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def generate_daily_digest():
    """Generate a summary digest of the last 24 hours."""
    conn = get_connection()
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    # Counts by project
    project_counts = conn.execute("""
        SELECT project, severity, COUNT(*) as cnt
        FROM audit_events WHERE timestamp >= ?
        GROUP BY project, severity ORDER BY project
    """, (cutoff,)).fetchall()

    # Total events
    total = conn.execute("""
        SELECT COUNT(*) FROM audit_events WHERE timestamp >= ?
    """, (cutoff,)).fetchone()[0]

    # Error count
    errors = conn.execute("""
        SELECT COUNT(*) FROM audit_events
        WHERE severity IN ('ERROR', 'CRITICAL') AND timestamp >= ?
    """, (cutoff,)).fetchone()[0]

    conn.close()

    digest = f"📊 **24h Audit Digest** ({datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC)\n"
    digest += f"Total Events: {total} | Errors: {errors}\n\n"

    current_project = None
    for row in project_counts:
        p, s, c = row['project'], row['severity'], row['cnt']
        if p != current_project:
            digest += f"**{p}:**\n"
            current_project = p
        icon = CentralAuditLogger.STATUS_ICONS.get(s, "📝")
        digest += f"  {icon} {s}: {c}\n"

    return digest

def get_stats():
    """Get audit trail statistics."""
    conn = get_connection()
    stats = {}
    stats['total_events'] = conn.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
    stats['projects'] = [r[0] for r in conn.execute("SELECT DISTINCT project FROM audit_events").fetchall()]
    stats['errors_24h'] = len(get_recent_errors(24))

    cutoff_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    stats['events_24h'] = conn.execute(
        "SELECT COUNT(*) FROM audit_events WHERE timestamp >= ?", (cutoff_24h,)
    ).fetchone()[0]

    conn.close()
    return stats


if __name__ == "__main__":
    print("=== Centralized Audit Trail ===")

    # Test logging from multiple "projects"
    sentinel_log = CentralAuditLogger("sovereign-sentinel")
    krypto_log = CentralAuditLogger("krypto")
    orch_log = CentralAuditLogger("orchestrator")

    sentinel_log.log("SYSTEM_START", "System", "Daily session initialized", "INFO")
    sentinel_log.log("SCAN_MARKET", "AAPL", "Price: $185.50, Volume: 55M", "INFO")
    sentinel_log.log("BUY_SIGNAL", "AAPL", "ORB breakout confirmed", "SUCCESS")
    sentinel_log.log("SPREAD_REJECT", "PENN", "Spread 0.8% > 0.05% limit", "WARNING")

    krypto_log.log("SYSTEM_START", "System", "Krypto engine online", "INFO")
    krypto_log.log("TICKER_FETCH", "XXBTZGBP", "BTC: £82,450", "INFO")
    krypto_log.log("NO_SIGNAL", "XETHZGBP", "ETH below VWAP, no entry", "INFO")

    orch_log.log("HEALTHCHECK", "System", "All systems operational", "SUCCESS")
    orch_log.log("BRAIN_SCAN", "System", "8 projects scanned", "INFO")

    # Test queries
    print("\n--- Recent Errors (should be 0) ---")
    errors = get_recent_errors(1)
    print(f"Errors in last hour: {len(errors)}")

    print("\n--- Daily Digest ---")
    print(generate_daily_digest())

    print("\n--- Stats ---")
    stats = get_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")

    print(f"\n💾 Database: {DB_PATH}")
