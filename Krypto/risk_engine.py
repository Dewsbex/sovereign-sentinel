import logging
import app_config

class RiskEngine:
    """
    Bi-Directional Risk Engine — dynamically scales risk per trade.
    
    Base: 1% equity risk per trade
    Win streak (3+): Scale up to 1.5%
    Loss streak (2+): Scale down to 0.5%
    Kill switch: 5% daily equity drawdown = halt all trading
    """
    def __init__(self):
        self.logger = logging.getLogger('trade_logger')
        self.max_daily_loss = app_config.MAX_DAILY_LOSS
        self.current_daily_pnl = 0.0
        self.starting_equity = 0.0  # Set on first trade
        self.kill_switch = False
        self.daily_trades = 0
        
        # Bi-Directional Streak Tracking
        self.consecutive_wins = 0
        self.consecutive_losses = 0
    
    def reset_daily_state(self):
        """Reset all tracking for new trading day."""
        self.current_daily_pnl = 0.0
        self.starting_equity = 0.0
        self.kill_switch = False
        self.daily_trades = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.logger.info("RISK ENGINE RESET: New trading day")

    def update_pnl(self, realized_pnl):
        """Update daily PnL and streak tracking after a trade closes."""
        self.current_daily_pnl += realized_pnl
        self.daily_trades += 1
        self.logger.info(f"RISK UPDATE: Daily PnL = {self.current_daily_pnl:.2f} ({self.daily_trades} trades)")
        
        # Update streak
        if realized_pnl > 0:
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            self.logger.info(f"WIN STREAK: {self.consecutive_wins}")
        elif realized_pnl < 0:
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            self.logger.info(f"LOSS STREAK: {self.consecutive_losses}")

        # Kill Switch: Flat max daily loss
        flat_limit = -abs(self.max_daily_loss)
        if self.current_daily_pnl <= flat_limit:
            self.kill_switch = True
            self.logger.critical(f"KILL SWITCH: PnL {self.current_daily_pnl:.2f} <= Limit {flat_limit:.2f}")
        
        # Kill Switch: 5% equity drawdown
        if self.starting_equity > 0:
            drawdown_pct = abs(self.current_daily_pnl) / self.starting_equity
            if self.current_daily_pnl < 0 and drawdown_pct >= 0.05:
                self.kill_switch = True
                self.logger.critical(
                    f"KILL SWITCH: 5% equity drawdown ({drawdown_pct:.1%}) — "
                    f"PnL={self.current_daily_pnl:.2f}, Starting Equity={self.starting_equity:.2f}"
                )

    def check_trade_allowed(self):
        if self.kill_switch:
            self.logger.warning("TRADING BLOCKED: Kill Switch Active")
            return False
        return True
    
    def get_dynamic_risk_pct(self):
        """
        Bi-directional risk scaling based on streak:
        - 3+ consecutive wins → 1.5% risk (ride the momentum)
        - 2+ consecutive losses → 0.5% risk (defensive)
        - Otherwise → base 1%
        """
        base = app_config.RISK_PER_TRADE_PERCENT  # 0.01 (1%)
        
        if self.consecutive_wins >= 3:
            risk = base * 1.5  # 1.5%
            self.logger.info(f"RISK SCALING UP: {risk*100:.1f}% (win streak: {self.consecutive_wins})")
            return risk
        
        if self.consecutive_losses >= 2:
            risk = base * 0.5  # 0.5%
            self.logger.info(f"RISK SCALING DOWN: {risk*100:.1f}% (loss streak: {self.consecutive_losses})")
            return risk
        
        return base

    def calculate_position_size(self, equity, entry_price, stop_loss):
        """
        Risk = Equity * dynamic_risk_pct
        Size = Risk / (Entry - Stop)
        """
        if entry_price <= stop_loss:
            return 0.0
        
        # Track starting equity for kill switch calculation
        if self.starting_equity == 0.0:
            self.starting_equity = equity
        
        risk_pct = self.get_dynamic_risk_pct()
        risk_amt = equity * risk_pct
        risk_per_share = entry_price - stop_loss
        units = risk_amt / risk_per_share
        
        self.logger.info(f"POSITION SIZE: {units:.6f} (risk={risk_pct*100:.1f}%, "
                        f"risk_amt={risk_amt:.2f}, per_unit={risk_per_share:.2f})")
        
        return units
