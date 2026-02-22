#!/usr/bin/env python3
"""
Credentials Manager
Centralized access for retrieving secrets from the OS Keyring.
Falls back to environment variables (legacy) if keyring entry is missing.
"""
import os
import logging
import keyring
import keyrings.alt
from dotenv import load_dotenv

# Load legacy .env for fallback
load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Credentials")

SYSTEM_NAME = "sovereign_sentinel"

def get_secret(key_name):
    """
    Retrieve a secret from the System Keyring.
    Fallback to OS environment variable if not found.
    """
    try:
        # 1. Try Keyring
        secret = keyring.get_password(SYSTEM_NAME, key_name)
        if secret:
            return secret
    except Exception as e:
        logger.debug(f"Keyring access failed for {key_name}: {e}")

    # 2. Fallback to Environment
    secret = os.getenv(key_name)
    if secret:
        # logger.warning(f"Using insecure fallback (Env/File) for: {key_name}")
        return secret
        
    return None

def set_secret(key_name, secret_value):
    """Sets a secret in the System Keyring."""
    if not secret_value:
        raise ValueError(f"Cannot set empty secret for {key_name}")
    try:
        keyring.set_password(SYSTEM_NAME, key_name, secret_value)
        logger.info(f"✅ Securely stored: {key_name}")
    except Exception as e:
        logger.error(f"❌ Failed to store {key_name}: {e}")
        raise
