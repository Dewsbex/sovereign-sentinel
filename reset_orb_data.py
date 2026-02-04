import json
import os
from datetime import datetime

DATA_FILE = 'data/orb_intel.json'

def clear_orb_data():
    """Resets the ORB Intelligence data for the next trading day."""
    empty_state = {
        "briefing": "", 
        "targets": [], 
        "last_updated": "RESET", 
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    with open(DATA_FILE, 'w') as f:
        json.dump(empty_state, f, indent=4)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ORB Data Cleared. Ready for next session.")

if __name__ == "__main__":
    clear_orb_data()
