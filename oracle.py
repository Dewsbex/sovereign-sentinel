from config import RISK_FREE_RATE, US_WHT

# ==============================================================================
# 5. THE "ORACLE PROTOCOL" (The Decision Engine)
# ==============================================================================

class Oracle:
    @staticmethod
    def gate_1_too_hard(sector):
        """Reject Biotech, Exploration, Turnarounds."""
        blacklist = ["Biotechnology", "Oil & Gas Exploration", "Turnarounds"]
        return sector not in blacklist

    @staticmethod
    def gate_2_moat(moat_type):
        """Reject 'Price Takers'."""
        return moat_type != "Price Taker"

    @staticmethod
    def gate_3_management(insider_activity):
        """Scan: Director Dealings (Open market buys = Skin in the Game)."""
        if "Empire Builder" in insider_activity:
            return False
        return "Open Market Buy" in insider_activity

    @staticmethod
    def gate_4_valuation(op_cash_flow, maint_capex, market_cap):
        """Net_Yield calculation."""
        if market_cap == 0: return 0
        net_yield = (op_cash_flow - maint_capex) / market_cap
        return net_yield

    @staticmethod
    def run_full_audit(ticker_data):
        """Applies all gates."""
        g1 = Oracle.gate_1_too_hard(ticker_data.get('sector'))
        g2 = Oracle.gate_2_moat(ticker_data.get('moat'))
        
        net_yield = Oracle.gate_4_valuation(
            ticker_data.get('ocf', 0),
            ticker_data.get('capex', 0),
            ticker_data.get('mcap', 1)
        )
        
        verdict = "FAIL"
        if g1 and g2 and net_yield > RISK_FREE_RATE:
            verdict = "PASS"
            
        return {
            "verdict": verdict,
            "net_yield": net_yield,
            "gates": {"g1": g1, "g2": g2, "g4": net_yield > RISK_FREE_RATE}
        }
