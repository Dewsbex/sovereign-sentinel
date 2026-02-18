class RiskBridge:
    """
    Implements the 'Sovereign Active Risk' formula.
    - Adaptive Spreads: Tighten spreads as P&L increases.
    - Unrealized Mirror Logic: Kill switch if drawdown > 3%.
    """
    def __init__(self, max_drawdown_pct=3.0):
        self.max_drawdown_pct = max_drawdown_pct
        self.base_spread = 0.005 # 0.5% default spread
        self.spread_modifier = 1.0

    def calculate_active_spread(self, realized_pl, current_equity):
        """
        Adaptive Spreads: Tighten the Grid or DCA spreads as realized P&L increases.
        Logic: If we are profitable (Realized P&L > 0), we can afford to be tighter/more aggressive or safer?
        Spec says: "Tighten the Grid... as realized P&L increases." 
        Interpretation: High P&L -> Smaller spread distance (take profit sooner/more entries?)
        """
        # Example Logarithmic decay of spread based on P&L
        # If P&L is 0, modifier is 1.0
        # If P&L is high, modifier decreases (spread tightens)
        
        if realized_pl <= 0:
            self.spread_modifier = 1.0
        else:
            # Simple linear reduction for demo: -10% spread per 1% P&L gain relative to equity?
            # Let's just say for every $100 profit, reduce spread by 1%
            # This is a heuristic placeholder.
            self.spread_modifier = max(0.5, 1.0 - (realized_pl / 10000.0))
            
        return self.base_spread * self.spread_modifier

    def check_unrealized_mirror(self, initial_equity, current_equity):
        """
        Unrealized Mirror Logic: Activate a fail-safe to stop the bot immediately 
        if the session drawdown exceeds 3%.
        """
        drawdown_pct = ((initial_equity - current_equity) / initial_equity) * 100
        
        if drawdown_pct > self.max_drawdown_pct:
            print(f"CRITICAL: Drawdown {drawdown_pct:.2f}% exceeds limit {self.max_drawdown_pct}%. Failsafe Triggered.")
            return False # Stop Trading
        
        return True # Continue Trading

if __name__ == "__main__":
    risk = RiskBridge()
    # Test Adaptive Spread
    print(f"Spread at 0 PL: {risk.calculate_active_spread(0, 1000)}")
    print(f"Spread at 5000 PL: {risk.calculate_active_spread(5000, 1000)}")
    
    # Test Mirror Logic
    print(f"Mirror Check (1000 -> 980): {risk.check_unrealized_mirror(1000, 980)}") # 2% DD - OK
    print(f"Mirror Check (1000 -> 960): {risk.check_unrealized_mirror(1000, 960)}") # 4% DD - FAIL
