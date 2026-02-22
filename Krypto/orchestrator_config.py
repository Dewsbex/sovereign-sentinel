import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Define absolute path to orchestrator master env
# This is for local development on Windows
ORCHESTRATOR_DIR = Path(r"C:\Users\steve\.gemini\antigravity\orchestrator")
MASTER_ENV_PATH = ORCHESTRATOR_DIR / "master.env"

def load_master_env():
    """
    Loads environment variables.
    Priority:
    1. Local .env file (Production/VPS)
    2. Master .env file (Local Dev)
    """
    # 1. Try local .env
    local_env = Path(".env")
    if local_env.exists():
        load_dotenv(local_env)
        # Check if critical keys are loaded, if so return
        if os.getenv("KRAKEN_API_KEY"):
            return True

    # 2. Try Master Env (Dev)
    if MASTER_ENV_PATH.exists():
        load_dotenv(MASTER_ENV_PATH)
        return True
    
    # 3. Last Resort: System Env (already loaded by os)
    return False

def get_secret(key, default=None):
    value = os.getenv(key)
    if value is None:
        load_master_env()
        value = os.getenv(key)
    return value if value is not None else default
