from datetime import datetime
from config import ENVIRONMENT, CGT_ALLOWANCE, DIV_ALLOWANCE

# ==============================================================================
# 4. THE "SOLAR CYCLE" (Daily Automation)
# ==============================================================================

class SolarCycle:
    def __init__(self):
        self.phase = "IDLE"
        self.logs = []

    def phase_1_pre_market(self):
        """07:50 GMT - Search: 'FTSE 100 futures', 'China PMI'."""
        self.phase = "PRE_MARKET"
        return {"futures": "Neutral", "macro_flags": []}

    def phase_2_london_validator(self, moves):
        """08:05 GMT - Noise Filter: Ignore moves < 0.3%."""
        self.phase = "LONDON_VALIDATOR"
        filtered = [m for m in moves if abs(m['pct']) > 0.003]
        return filtered

    def phase_3_transatlantic_pivot(self):
        """13:30 GMT - Red Folder Alert: Lock Buy buttons if US Macro data imminent."""
        self.phase = "TRANSATLANTIC_PIVOT"
        return {"macro_lock": False}

    def phase_4_global_auditor(self):
        """21:00 GMT - Stale Order Sweeper, High-Water Mark."""
        self.phase = "GLOBAL_AUDITOR"
        return {"stale_orders": 0, "hwm_breaches": []}

    def phase_4b_tax_logic_fork(self, data):
        """Context dependent tax auditing."""
        report = {}
        if ENVIRONMENT == "ISA":
            report = {
                "limit_sentinel": "Active",
                "days_to_april_5": (datetime(2026, 4, 5) - datetime.now()).days,
                "loss_harvesting": "N/A (Tax Free)",
                "bed_n_breakfast": "Clear (No Restriction)"
            }
        else: # GIA
            report = {
                "loss_harvesting": "Monitor (>£3k CGT)",
                "div_tax_watch": f"Usage vs £500 limit",
                "bb_guard": "30-day Wash Sale Warning Active"
            }
        return report

    def phase_5_weekend_audit(self):
        """Thesis Maintenance: Compare current metrics vs. Thesis Locker."""
        self.phase = "WEEKEND_AUDIT"
        return {"thesis_drift": False}
