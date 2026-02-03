import json
import os
import subprocess
from datetime import datetime

# 1. Mock the BOT's internal state as if it just finished a scan
mock_orb_levels = {
    "NOW": {"high": 112.17, "low": 109.55, "rvol": 8.89, "last_price": 110.63},
    "NVDA": {"high": 185.95, "low": 182.78, "rvol": 1.91, "last_price": 181.32},
    "COIN": {"high": 187.24, "low": 182.60, "rvol": 2.59, "last_price": 183.52},
    "MSTR": {"high": 139.62, "low": 136.25, "rvol": 1.62, "last_price": 137.93},
    "APP": {"high": 483.30, "low": 459.91, "rvol": 3.11, "last_price": 456.74}
}

def generate_mock_intel():
    print("[>] Generating Mock Intelligence...")
    sorted_targets = sorted(
        [{'ticker': t, **levels} for t, levels in mock_orb_levels.items()],
        key=lambda x: x['rvol'], 
        reverse=True
    )
    
    top = sorted_targets[0]
    ticker_list = ", ".join([x['ticker'] for x in sorted_targets])
    
    today_date = datetime.utcnow().strftime("%d/%m/%Y")
    
    brief = f"Set alerts for these exact prices today. Based on the High of the Day established in the first 15 minutes of {today_date}. Buy when price breaks above these levels.\n\n"
    brief += f"**Priority**: Watch **ServiceNow ({top['ticker']})** first. As has the highest volume ({top['rvol']:.2f}x) and is closest to the trigger. "
    brief += "\n\n**Operational Tip**: In the Trading 212 app, set the alert slightly below these numbers (e.g., set NVDA at $185.80) so you have time to unlock your phone and check the spread."

    intel = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "briefing": brief,
        "targets": [
            {
                "ticker": t,
                "company": t, # Fallback
                "trigger": levels['high'],
                "alert": levels['high'] * 0.999,
                "stop": levels['low'],
                "rvol": levels['rvol'],
                "gap_to_fill": abs(levels['last_price'] - levels['high'])
            } for t, levels in mock_orb_levels.items()
        ]
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/orb_intel.json", "w") as f:
        json.dump(intel, f, indent=4)
    print("[SUCCESS] orb_intel.json created.")

def run_dashboard_flow():
    print("[>] Running Dashboard Pipeline...")
    # Skip generate_isa_portfolio.py because it needs API keys
    # We've already mocked the intel. Now we just need to make sure live_state has it.
    
    if os.path.exists("live_state.json"):
        with open("live_state.json", "r") as f:
            state = json.load(f)
        
        with open("data/orb_intel.json", "r") as f:
            intel = json.load(f)
            
        state["orb_intel"] = intel
        with open("live_state.json", "w") as f:
            json.dump(state, f, indent=4)
        print("[SUCCESS] live_state.json updated with intel.")
        
    print("[>] Rendering index.html...")
    subprocess.run(["python", "generate_static.py"])
    print("[FINISH] Test complete. Open index.html to see the results.")

if __name__ == "__main__":
    generate_mock_intel()
    run_dashboard_flow()
