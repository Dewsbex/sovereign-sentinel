import keyring
import keyrings.alt
import logging

logging.basicConfig(level=logging.DEBUG)

print(f"Keyring Config: {keyring.get_keyring()}")
try:
    val = keyring.get_password("sovereign_sentinel", "TRADING212_API_KEY")
    print(f"TRADING212_API_KEY found: {'YES' if val else 'NO'}")
    if val:
        print(f"Value length: {len(val)}")
        print(f"Value prefix: {val[:4]}...")
except Exception as e:
    print(f"Error: {e}")
