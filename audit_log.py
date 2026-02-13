import csv
import os
import time
from datetime import datetime
from typing import Optional

class AuditLogger:
    """
    Persistent CSV Audit Logger for Sovereign Sentinel.
    Tracks every action, decision, and process state.
    Thread-safe(ish) and ensures flush to disk.
    """
    
    def __init__(self, process_name: str = "Unknown"):
        self.process_name = process_name
        self.log_dir = "data"
        self.log_file = os.path.join(self.log_dir, "audit_log.csv")
        self._ensure_log_exists()
        
    def _ensure_log_exists(self):
        """Creates the log file with headers if it doesn't exist."""
        os.makedirs(self.log_dir, exist_ok=True)
        
        if not os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Process", "Action", "Target", "Details", "Status"])
                    f.flush()
                    os.fsync(f.fileno())
            except Exception as e:
                print(f"⚠️ Failed to create audit log: {e}")

    def log(self, action: str, target: str = "-", details: str = "", status: str = "INFO"):
        """
        Logs an event to the persistent CSV.
        
        Args:
            action (str): The high-level action (e.g., "SCAN_MARKET", "BUY_SIGNAL", "ERROR").
            target (str): The ticker or object being acted upon (e.g., "AAPL", "System").
            details (str): specific details or parameters.
            status (str): "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL", "HEARTBEAT".
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Console output for immediate visibility (skip HEARTBEATS to avoid spamming console if desired, 
        # but user asked for "every action", so we print it.)
        icon = self._get_status_icon(status)
        
        if status != "HEARTBEAT":
            print(f"{icon} [{timestamp}] {self.process_name} | {action}: {target} - {details}")
        
        try:
            # retry logic for file contention
            attempts = 3
            while attempts > 0:
                try:
                    with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp, self.process_name, action, target, details, status])
                        f.flush()
                        os.fsync(f.fileno()) # Force write to disk
                    break
                except PermissionError:
                    attempts -= 1
                    time.sleep(0.1)
                except Exception as e:
                    print(f"⚠️ Failed to write to audit log: {e}")
                    break
                    
        except Exception as e:
            print(f"⚠️ Critical Audit Failure: {e}")

    def _get_status_icon(self, status: str) -> str:
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🔥",
            "HEARTBEAT": "💓"
        }
        return icons.get(status.upper(), "📝")
