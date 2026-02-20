import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("SessionLedger")

class SessionLedger:
    """
    The 'Ground Truth' ledger for Job C (Sniper/Sentinel) trades.
    Ensures that the 5% process only manages assets it explicitly purchased.
    """
    def __init__(self, filepath='data/session_ledger.json'):
        self.filepath = filepath
        self.data = self._load_ledger()

    def _load_ledger(self) -> Dict[str, Any]:
        """Loads the ledger from disk, ensuring it exists."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            return {"date": datetime.utcnow().strftime('%Y-%m-%d'), "trades": {}}
        
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                # We do NOT auto-reset here. We want a persistent audit trail.
                # But Job C logic might only care about trades from 'today'.
                return data
        except Exception as e:
            logger.error(f"Ledger Load Error: {e}")
            return {"date": datetime.utcnow().strftime('%Y-%m-%d'), "trades": {}}

    def _save_ledger(self):
        """Atomic write to prevent corruption."""
        temp_path = self.filepath + ".tmp"
        try:
            with open(temp_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            os.replace(temp_path, self.filepath)
        except Exception as e:
            logger.error(f"Ledger Save Error: {e}")

    def record_purchase(self, ticker: str, quantity: float, price: float, side: str = "BUY"):
        """Records a new entry in the session ledger."""
        if ticker not in self.data["trades"]:
            self.data["trades"][ticker] = []
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "side": side,
            "quantity": quantity,
            "price": price,
            "session_date": datetime.utcnow().strftime('%Y-%m-%d')
        }
        
        self.data["trades"][ticker].append(entry)
        self._save_ledger()
        logger.info(f"LEDGER: Recorded {side} for {ticker}: {quantity} @ {price}")

    def get_session_quantity(self, ticker: str) -> float:
        """Returns the total quantity of a ticker purchased in the CURRENT session."""
        today = datetime.utcnow().strftime('%Y-%m-%d')
        total = 0.0
        
        if ticker in self.data["trades"]:
            for trade in self.data["trades"][ticker]:
                if trade["session_date"] == today:
                    if trade["side"] == "BUY":
                        total += trade["quantity"]
                    else:
                        total -= trade["quantity"]
        
        return max(0.0, total)

    def is_job_c_holding(self, ticker: str) -> bool:
        """Checks if Job C has ANY active quantity in this ticker for the session."""
        return self.get_session_quantity(ticker) > 0

    def get_audit_trail(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns the full history of trades for audit."""
        if ticker:
            return self.data["trades"].get(ticker, [])
        return self.data["trades"]

if __name__ == "__main__":
    # Test Ledger
    ledger = SessionLedger('data/test_ledger.json')
    ledger.record_purchase("AAPL", 5, 150.0)
    print(f"AAPL Quantity: {ledger.get_session_quantity('AAPL')}")
    ledger.record_purchase("AAPL", 5, 145.0, "SELL")
    print(f"AAPL Quantity after Sell: {ledger.get_session_quantity('AAPL')}")
