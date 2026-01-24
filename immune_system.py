import time
from datetime import datetime, timedelta

# ==============================================================================
# 2. CRITICAL SAFETY INFRASTRUCTURE (The "Immune System")
# ==============================================================================

class ImmuneSystem:
    def __init__(self):
        self.alerts = []
        self.locks = []

    def check_pessimist_protocol(self, api_status):
        """Standard: API Error -> Lock Execution."""
        if api_status != "OK":
            self.locks.append("API_DISRUPTED")
            return False
        return True

    def check_stock_split_guard(self, ticker, price_deviation):
        """>20% deviation blocks signals until verified."""
        if abs(price_deviation) > 0.20:
            self.locks.append(f"SPLIT_GUARD_{ticker}")
            self.alerts.append(f"⚠️ SPLIT GUARD: {ticker} deviation > 20%. Manual verification required.")
            return False
        return True

    def check_earnings_radar(self, ticker, days_to_earnings):
        """Hard-blocks 'Buy' <7 days before earnings."""
        if days_to_earnings is not None and days_to_earnings < 7:
            return "BLOCK_BUY"
        return "CLEAR"

    def check_falling_knife(self, ticker, price_drop_30m):
        """Wait 30 mins after >1% drop. Alert only on stabilization."""
        if price_drop_30m > 0.01:
            return "KNIFE_ACTIVE"
        return "STEADY"

    def notification_governor(self, ticker, last_notif_time, price_move):
        """Mute ticker for 4 hours unless price moves >3%."""
        if last_notif_time:
            time_diff = datetime.now() - last_notif_time
            if time_diff < timedelta(hours=4) and abs(price_move) < 0.03:
                return False
        return True

    def connectivity_heartbeat(self, latency_ms):
        """Sync check at 07:55 GMT. Latency limit: 2000ms."""
        if latency_ms > 2000:
            return "LATENCY_WARNING"
        return "HEARTBEAT_HEALTHY"

def get_immune_report():
    # Placeholder for actual data collection
    return {
        "heartbeat": "HEALTHY",
        "locks": [],
        "active_alerts": []
    }
