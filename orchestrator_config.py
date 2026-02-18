import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Define absolute path to orchestrator master env
ORCHESTRATOR_DIR = Path(r"C:\Users\steve\.gemini\antigravity\orchestrator")
MASTER_ENV_PATH = ORCHESTRATOR_DIR / "master.env"

def load_master_env():
    """
    Loads environment variables from the centralized master.env file.
    """
    if not MASTER_ENV_PATH.exists():
        print(f"WARNING: Master env file not found at {MASTER_ENV_PATH}")
        return False
    
    # Load .env file
    load_dotenv(MASTER_ENV_PATH)
    return True

def get_secret(key, default=None):
    value = os.getenv(key)
    if value is None:
        load_master_env()
        value = os.getenv(key)
    if value is None:
        return default
    return value
