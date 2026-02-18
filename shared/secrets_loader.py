import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Define paths to check for master.env
PATHS_TO_CHECK = [
    # 1. Local Windows (Task Context)
    Path(r"C:\Users\steve\.gemini\antigravity\orchestrator\master.env"),
    # 2. Linux VPS standard location (if we sync it there)
    Path.home() / ".gemini" / "antigravity" / "orchestrator" / "master.env",
    # 3. Current directory .env (fallback)
    Path(".env"),
    # 4. Parent directory .env (fallback)
    Path("../.env")
]

def load_master_env():
    """
    Loads environment variables from the centralized master.env file.
    Only loads variables that are not already set in the environment.
    """
    loaded = False
    for path in PATHS_TO_CHECK:
        if path.exists():
            load_dotenv(path)
            loaded = True
            # print(f"DEBUG: Loaded env from {path}")
            break
            
    if not loaded:
        # print("WARNING: No master.env or local .env found.")
        return False
    
    return True

def get_secret(key, default=None):
    """
    Retrieves a secret from the environment, attempting to load master env if not found.
    """
    value = os.getenv(key)
    if value is None:
        load_master_env()
        value = os.getenv(key)
    
    if value is None:
        return default
    return value

def get_telegram_creds(project="sentinel"):
    """
    Helper to get Telegram credentials for specific projects.
    project: "sentinel", "krypto", or "hub" (defaults to sentinel)
    """
    load_master_env()
    
    if project.lower() == "krypto":
        token = os.getenv("TELEGRAM_TOKEN_KRYPTO")
        chat_id = os.getenv("TELEGRAM_CHAT_ID_KRYPTO")
    else:
        # Default to Sentinel for now, or Hub if we make one
        token = os.getenv("TELEGRAM_TOKEN_SENTINEL")
        chat_id = os.getenv("TELEGRAM_CHAT_ID_SENTINEL")
        
    return token, chat_id
