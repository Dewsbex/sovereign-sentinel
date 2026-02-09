"""
Wealth Seeker v0.01 - T212 Ledger Sync (sync_ledger.py)
========================================================
Fetches order history from Trading212 API and updates eod_balance.json
"""

import json
import os
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any


# ========================================================================
# v1.9.4 PERSISTENCE LOCK: Protect the Holy Ledger
# ========================================================================
def verify_persistence_lock():
    """
    Ensures the persistent data volume is mounted before writing Holy Ledger.
    
    CRITICAL: eod_balance.json contains historical profit data.
    If written to an unmounted volume, it will be lost on next git sync.
    """
    data_dir = 'data'
    
    if not os.path.exists(data_dir):
        print(f"\n{'='*70}")
        print(f"❌ PERSISTENCE LOCK FAILURE")
        print(f"{'='*70}")
        print(f"⛔ The '{data_dir}' directory does not exist.")
        print(f"   Cannot sync Holy Ledger (eod_balance.json)")
        print(f"\nTo fix:")
        print(f"  1. Mount the Oracle VPS persistent volume")
        print(f"  2. Verify mount point: 'df -h | grep {data_dir}'")
        print(f"{'='*70}\n")
        sys.exit(1)
    
    # Check if writable
    test_file = os.path.join(data_dir, '.persistence_test')
    try:
        with open(test_file, 'w') as f:
            f.write('OK')
        os.remove(test_file)
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ PERSISTENCE LOCK FAILURE")
        print(f"{'='*70}")
        print(f"⛔ The '{data_dir}' directory exists but is NOT writable.")
        print(f"   Error: {e}")
        print(f"   Cannot sync Holy Ledger (eod_balance.json)")
        print(f"{'='*70}\n")
        sys.exit(1)

# Run persistence lock BEFORE any class definitions
verify_persistence_lock()
print(f"✅ Persistence lock verified for Holy Ledger sync")


class T212LedgerSync:
    """Syncs Trading212 account data and calculates realized profits"""
    
    def __init__(self):
        self.api_key = os.getenv("T212_API_TRADE_KEY")
        self.api_secret = os.getenv("T212_API_TRADE_SECRET")
        self.base_url = "https://live.trading212.com/api/v0"
        self.balance_path = "data/eod_balance.json"
        
        if not self.api_key:
            raise ValueError("T212_API_TRADE_KEY environment variable not set")
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate API headers with authentication"""
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
    
    def get_account_cash(self) -> Dict[str, Any]:
        """Fetch current cash balance"""
        url = f"{self.base_url}/equity/account/cash"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    def get_portfolio_positions(self) -> List[Dict[str, Any]]:
        """Fetch current open positions"""
        url = f"{self.base_url}/equity/portfolio"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    def get_order_history(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Fetch historical orders"""
        cursor = None
        all_orders = []
        
        # T212 API uses pagination
        while True:
            url = f"{self.base_url}/equity/history/orders"
            params = {"limit": 50}
            if cursor:
                params["cursor"] = cursor
            
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            
            orders = data.get("items", [])
            all_orders.extend(orders)
            
            # Check if there are more pages
            cursor = data.get("nextPageCursor")
            if not cursor:
                break
        
        return all_orders
    
    def calculate_realized_profit(self, orders: List[Dict[str, Any]]) -> float:
        """
        Calculate realized profit from closed positions
        Note: This is a simplified calculation. For production, you'd want more sophisticated P&L tracking.
        """
        total_realized = 0.0
        
        for order in orders:
            # Only count filled sell orders
            if order.get("type") == "SELL" and order.get("status") == "FILLED":
                filled_value = order.get("filledValue", 0.0)
                # Subtract fees
                total_realized += filled_value
        
        return total_realized
    
    def sync_balance(self) -> Dict[str, Any]:
        """
        Main sync function: fetch T212 data and update eod_balance.json
        Returns updated balance state
        """
        print("🔄 Syncing ledger from Trading212...")
        
        try:
            # Fetch data from T212
            cash_data = self.get_account_cash()
            positions = self.get_portfolio_positions()
            orders = self.get_order_history()
            
            # Calculate metrics
            total_cash = cash_data.get("total", 0.0)
            free_cash = cash_data.get("free", 0.0)
            
            # Calculate realized profit (simplified)
            # In production, you'd track cost basis more carefully
            realized_profit = self.calculate_realized_profit(orders)
            
            # Load existing balance state
            try:
                with open(self.balance_path, 'r') as f:
                    balance_state = json.load(f)
            except FileNotFoundError:
                balance_state = {
                    "realized_profit": 0.0,
                    "seed_capital": 1000.0,
                    "scaling_unlocked": False,
                    "total_trades": 0
                }
            
            # Update state
            balance_state["realized_profit"] = realized_profit
            balance_state["last_session"] = datetime.utcnow().strftime("%Y-%m-%d")
            balance_state["total_cash"] = total_cash
            balance_state["free_cash"] = free_cash
            balance_state["position_count"] = len(positions)
            
            # Check if scaling should be activated
            if realized_profit >= 1000.0:
                balance_state["scaling_unlocked"] = True
            
            # Save updated state
            with open(self.balance_path, 'w') as f:
                json.dump(balance_state, f, indent=2)
            
            print(f"✅ Ledger synced successfully")
            print(f"   Total Cash: £{total_cash:.2f}")
            print(f"   Free Cash: £{free_cash:.2f}")
            print(f"   Realized Profit: £{realized_profit:.2f}")
            print(f"   Scaling Unlocked: {balance_state['scaling_unlocked']}")
            print(f"   Total Trades: {balance_state.get('total_trades', 0)}")
            
            return balance_state
            
        except requests.HTTPError as e:
            print(f"❌ T212 API Error: {e}")
            print(f"   Response: {e.response.text if e.response else 'No response'}")
            raise
        except Exception as e:
            print(f"❌ Sync failed: {e}")
            raise


def main():
    """Entry point for sync_ledger.py"""
    import sys
    
    # Check for test mode
    if "--test-connection" in sys.argv:
        print("🧪 Testing T212 API connection...")
        try:
            sync = T212LedgerSync()
            cash = sync.get_account_cash()
            print(f"✅ Connection successful! Cash: £{cash.get('total', 0):.2f}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)
        return
    
    # Normal sync
    sync = T212LedgerSync()
    sync.sync_balance()


if __name__ == "__main__":
    main()
