import os
from orb_messenger import ORBMessenger

def verify():
    # Test 1: DEMO mode (default)
    os.environ['ENV'] = 'DEMO'
    msg_demo = ORBMessenger()
    print(f"DEMO Prefix check: {msg_demo.prefix}")
    assert msg_demo.prefix == "(DEMO)", f"Expected (DEMO), got {msg_demo.prefix}"
    
    # Test 2: LIVE mode
    os.environ['ENV'] = 'LIVE'
    msg_live = ORBMessenger()
    print(f"LIVE Prefix check: {msg_live.prefix}")
    assert msg_live.prefix == "(LIVE)", f"Expected (LIVE), got {msg_live.prefix}"
    
    print("[SUCCESS] Telegram Telemetry Prefix Verified.")

if __name__ == "__main__":
    verify()
