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
        self.scalper_ledger_file = "data/eod_balance.json"
        self.scalper_state = {} 
        self.load_config()
        self.load_state()
        self.load_scalper_ledger()

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
        self.save_state()

    def load_scalper_ledger(self):
        if not os.path.exists(self.scalper_ledger_file):
            # init new ledger
            self.scalper_state = {
                "initial_seed": self.config['risk'].get('seed_capital', 1000.0),
                "current_balance": self.config['risk'].get('seed_capital', 1000.0),
                "history": []
            }
            self.save_scalper_ledger()
        else:
            try:
                with open(self.scalper_ledger_file, 'r') as f:
                    self.scalper_state = json.load(f)
            except:
                self.scalper_state = {"current_balance": 1000.0}

    def save_scalper_ledger(self):
        with open(self.scalper_ledger_file, 'w') as f:
            json.dump(self.scalper_state, f, indent=4)

    def get_allocation_amount(self):
        """Returns the £ amount to allocate to a single trade based on v32.60 'Scale Earned' rule."""
        if self.state.get('circuit_breaker_tripped'):
            return 0.0
            
        seed = self.config['risk'].get('seed_capital', 1000.0)
        
        # v32.60 Logic: Check INDEPENDENT Scalper Ledger
        scalper_balance = self.scalper_state.get('current_balance', seed)
        cumulative_profit = scalper_balance - seed
        
        # Scale Gate: ONLY if Cumulative Profit >= £1,000
        if cumulative_profit >= 1000.0:
            # Scale Mode: 5% of Total Account Equity
            alloc_pct = 0.05
            amount = self.state['current_equity'] * alloc_pct
            logger.info(f"Allocation Scale UNLOCKED: Using 5% of Total Equity (£{amount:.2f})")
        else:
            # Seed Mode: Hard Cap at £1,000 (Active Risk Capital)
            # Interpretation: We risk the Seed, not the Profit.
            # Spec: "If cumulative_profit < 1000.00, set active_risk = 1000.00"
            amount = 1000.0 
            logger.info(f"Allocation Seed Mode: Hard Cap £{amount:.2f} (Profit: £{cumulative_profit:.2f})")
            
        return round(amount, 2)
        
    def check_circuit_breaker(self):
        """v32.60: Disable Job C if Session Loss >= £1,000"""
        today_pnl = self.state['daily_performance']['pnl']
        if today_pnl <= -1000.0:
            logger.critical(f"🛑 CIRCUIT BREAKER TRIPPED: Session Loss £{today_pnl} >= £1,000 limit.")
            self.state['circuit_breaker_tripped'] = True
            self.save_state()
            return True
        return False

    def record_trade(self, ticker, pnl):
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        if self.state['daily_performance']['date'] != today:
             self.state['daily_performance'] = {"date": today, "pnl": 0.0, "trades_taken": 0}
        
        self.state['daily_performance']['pnl'] += pnl
        self.state['daily_performance']['trades_taken'] += 1
        self.update_equity(self.state['current_equity'] + pnl)
        
        # Update Scalper Independent Ledger
        if 'current_balance' in self.scalper_state:
            self.scalper_state['current_balance'] += pnl
            self.scalper_state['history'].append({
                "date": today,
                "ticker": ticker,
                "pnl": pnl,
                "balance": self.scalper_state['current_balance']
            })
            self.save_scalper_ledger()

if __name__ == "__main__":
    # Internal Logic Test
    mgr = SovereignStateManager()
    print(f"Current Equity: {mgr.state['current_equity']}")
    print(f"Allocation: {mgr.get_allocation_amount()}")
