import json
import os
import time
import sys
import datetime

# Set stdout to UTF-8 to handle emojis on Windows
sys.stdout.reconfigure(encoding='utf-8')

# --- Constants ---
CONFIG_FILE = "config.json"
DEFAULT_CAP = 500.0

# --- Core Logic ---

def load_config():
    """Loads the strategy configuration from config.json."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Warning: {CONFIG_FILE} not found. Using default cap of £{DEFAULT_CAP}.")
        return {"STRATEGY_CAP_GBP": DEFAULT_CAP}
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config
    except Exception as e:
        print(f"Error loading config: {e}. Using default cap.")
        return {"STRATEGY_CAP_GBP": DEFAULT_CAP}

def check_strategy_limit(proposed_trade_value, current_cap):
    """
    Enforces the Strategy Capital Ceiling.
    Returns (Allowed, AdjustedValue, Reason)
    """
    if proposed_trade_value <= current_cap:
        return True, proposed_trade_value, "Within Limit"
    
    # Logic: If trade exceeds cap, we scale down or abort. 
    # For this spec: "Force a 'Down-Size' to fit the limit or aborts."
    # We will Down-Size to exactly the cap.
    
    return False, current_cap, f"CAPPED: Proposed £{proposed_trade_value} > Limit £{current_cap}"

def place_market_order(ticker, value):
    """
    Stub for placing a market order. 
    In a real scenario, this would call the Trading 212 API.
    """
    print(f"[{datetime.datetime.now()}] 🚀 EXECUTING MARKET ORDER: {ticker} for £{value}")

def run_orb_sidecar():
    print("🛡️ ORB Sidecar: Starting Titan Shield initialization...")
    
    # 1. Load Hard Deck
    config = load_config()
    strategy_limit = float(config.get("STRATEGY_CAP_GBP", DEFAULT_CAP))
    print(f"💰 Strategy Capital Ceiling: £{strategy_limit}")

    # 2. Simulated High-Frequency Poller (Verification Logic)
    # In production, this runs a while loop checking WebSocket prices.
    # Here we simulate a trade trigger to verify the Ceiling Guard.
    
    print("\n--- Simulated Trading Session ---")
    
    # Scenario A: Trade within limit
    proposed_trade_a = 150.00
    print(f"\n🔍 Analyzing Trade A: £{proposed_trade_a}...")
    allowed, final_value, reason = check_strategy_limit(proposed_trade_a, strategy_limit)
    if allowed:
        place_market_order("TSLA", final_value)
    else:
        print(f"⚠️ {reason}. Adjusting to £{final_value}...")
        place_market_order("TSLA", final_value)

    # Scenario B: Trade exceeding limit (The "Ghost Test")
    proposed_trade_b = 600.00
    print(f"\n🔍 Analyzing Trade B: £{proposed_trade_b}...")
    allowed, final_value, reason = check_strategy_limit(proposed_trade_b, strategy_limit)
    
    if allowed:
        place_market_order("NVDA", final_value)
    else:
        print(f"⚠️ {reason}. Down-Sizing order...")
        place_market_order("NVDA", final_value)
        
    print("\n✅ Titan Shield logic verification complete.")

if __name__ == "__main__":
    run_orb_sidecar()
