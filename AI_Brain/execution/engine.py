import time
import sys
import os
from datetime import datetime

# Adjust path to find sibling modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from execution.kraken_client import KrakenClient
    from risk.bridge import RiskBridge
    from governance.auditor import AuditorAgent
except ImportError:
    # Fallback for running from root
    from AI_Brain.execution.kraken_client import KrakenClient
    from AI_Brain.risk.bridge import RiskBridge
    from AI_Brain.governance.auditor import AuditorAgent

class RemoteEngine:
    """
    Primary execution environment for 24/7 trading and automation (Oracle Ubuntu).
    Integrates Kraken Client, Risk Bridge, and Auditor Agent.
    """
    def __init__(self):
        print("Initializing AI Brain Remote Engine...")
        self.client = KrakenClient()
        self.risk = RiskBridge()
        self.auditor = AuditorAgent()
        self.running = True
        self.initial_equity = None
        
        # Load keys from Kryptoenv if needed (KrakenClient handles env vars)
        # self._load_env() 
        
    def _load_env(self):
        # Placeholder for explicit env loading if not handled by systemd/shell
        pass

    def run(self):
        print("Krypto: Engine Started. Waiting for signals...")
        
        # Startup Checks
        try:
            # Check connection
            server_time = self.client.get_server_time()
            if not server_time:
                 print("Krypto: Critical - Failed to connect to Kraken. Retrying in 60s...")
                 time.sleep(60)
                 return 
            print(f"Krypto: Kraken Connection OK. Server Time: {server_time['rfc1123']}")
            
            # Initial Equity Snapshot for Risk Bridge
            balance = self.client.get_trade_balance()
            if balance:
                self.initial_equity = float(balance.get('eb', 0.0)) # 'eb' = equity balance equivalent
                print(f"Krypto: Initial Equity: ${self.initial_equity:.2f}")
            else:
                # If keys are bad or paper mode mock, default to safe value or 0
                self.initial_equity = 10000.0 
                print("Krypto: Warning - Could not fetch balance. Using Mock Equity $10000.00")

        except Exception as e:
            print(f"Krypto: Startup Exception: {e}")

        # Main Loop
        while self.running:
            try:
                # 1. Heartbeat / State Parity Check
                # (Could check for git updates here roughly or rely on external process)
                
                # 2. Risk Check (The Risk Bridge)
                current_balance = self.client.get_trade_balance()
                current_equity = float(current_balance.get('eb', 0.0)) if current_balance else self.initial_equity
                
                if not self.risk.check_unrealized_mirror(self.initial_equity, current_equity):
                    print("Krypto: ⛔ STOP BOT - Risk Bridge triggered kill switch.")
                    self.stop()
                    break

                # 3. Execution Logic (Scan -> Audit -> Trade)
                # Placeholder for strategy scanner
                # signal = strategy.scan()
                signal = None # No component built yet for strategy scanning
                
                if signal:
                    # 4. Governance (Auditor)
                    if self.auditor.audit_signal(signal):
                        # 5. Execute
                        print(f"Krypto: Executing Trade: {signal}")
                        # resp = self.client.add_order(...)
                        # print(resp)
                    else:
                        print("Krypto: Trade rejected by Auditor.")

                # Sleep (Poll rate)
                time.sleep(60) 

            except KeyboardInterrupt:
                self.stop()
            except Exception as e:
                print(f"Krypto: Loop Error: {e}")
                time.sleep(10)

    def stop(self):
        self.running = False
        print("Krypto: Engine Stopped.")

if __name__ == "__main__":
    engine = RemoteEngine()
    engine.run()
