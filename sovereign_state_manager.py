import json
import os
import datetime
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SovereignState")

class SovereignStateManager:
    def __init__(self, state_file="data/ledger_state.json", config_file="config/orb_config.json"):
        self.state_file = state_file
        self.config_file = config_file
        self.state = {}
        self.config = {}
        self.load_config()
        self.load_state()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def load_state(self):
        if not os.path.exists(self.state_file):
            logger.warning("State file not found. Creating new state.")
            self.reset_state()
        else:
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                self.reset_state()

    def reset_state(self):
        self.state = {
            "high_water_mark": self.config['risk']['initial_capital'],
            "current_equity": self.config['risk']['initial_capital'],
            "last_updated": datetime.datetime.utcnow().isoformat(),
            "daily_performance": {
                "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                "pnl": 0.0,
                "trades_taken": 0
            },
            "active_positions": [],
            "circuit_breaker_tripped": False
        }
        self.save_state()

    def save_state(self):
        self.state['last_updated'] = datetime.datetime.utcnow().isoformat()
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=4)
            logger.info("State saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def update_equity(self, new_equity):
        self.state['current_equity'] = float(new_equity)
        
        # Update HWM
        if self.state['current_equity'] > self.state['high_water_mark']:
            self.state['high_water_mark'] = self.state['current_equity']
            logger.info(f"🚀 NEW HIGH WATER MARK: {self.state['high_water_mark']}")

        # Check Circuit Breaker
        drawdown = (self.state['high_water_mark'] - self.state['current_equity']) / self.state['high_water_mark'] * 100
        max_dd = self.config['risk']['max_drawdown_percent']
        
        if drawdown >= max_dd:
            self.state['circuit_breaker_tripped'] = True
            logger.critical(f"🛑 CIRCUIT BREAKER TRIGGERED! Drawdown: {drawdown:.2f}% (Limit: {max_dd}%)")

        self.save_state()

    def get_allocation_amount(self):
        """Returns the £ amount to allocate to a single trade based on configuration."""
        if self.state['circuit_breaker_tripped']:
            return 0.0
            
        alloc_pct = self.config['risk']['trade_allocation_percent'] / 100.0
        # Allocate based on current equity (or HWM? Conservative is Current)
        amount = self.state['current_equity'] * alloc_pct
        return round(amount, 2)

    def record_trade(self, ticker, pnl):
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        if self.state['daily_performance']['date'] != today:
             self.state['daily_performance'] = {"date": today, "pnl": 0.0, "trades_taken": 0}
        
        self.state['daily_performance']['pnl'] += pnl
        self.state['daily_performance']['trades_taken'] += 1
        self.update_equity(self.state['current_equity'] + pnl)

if __name__ == "__main__":
    # Internal Logic Test
    mgr = SovereignStateManager()
    print(f"Current Equity: {mgr.state['current_equity']}")
    print(f"Allocation: {mgr.get_allocation_amount()}")
