#!/usr/bin/env python3
"""
Setup Keyring (One-Time Script)
Populates the OS Keyring with Sovereign Sentinel credentials.
"""
import sys
import getpass
from credentials_manager import set_secret

def main():
    print("Sovereign Sentinel Keyring Setup")
    print("-----------------------------------")
    print("This script will securely store your API keys in the OS Credential Locker.")
    print("Existing values will be overwritten.\n")

    # Defined keys to prompt for
    keys_to_set = [
        "GOOGLE_API_KEY",
        "TELEGRAM_TOKEN",
        "TELEGRAM_CHAT_ID",
        "TELEGRAM_TOKEN_KRYPTO", 
        "TELEGRAM_CHAT_ID_KRYPTO",
        "KRAKEN_API_KEY",
        "KRAKEN_SECRET",
        "TRADING212_API_KEY",
        "ALPHA_VANTAGE_API_KEY",
        # Add others as needed
    ]
    
    # Batch mode for known keys (populated by Antigravity)
    # This dictionary is populated based on user provided keys
    known_secrets = {
        "GOOGLE_API_KEY": "AIzaSyDcKN_gsJV0UNGBMjnXGjSzVpoMJXq4EQ4",
        "TELEGRAM_TOKEN": "8585563319:AAH0wx3peZycxqG1KC9q7FMuSwBw2ps1TGA",
        "TELEGRAM_CHAT_ID": "7675773887",
        # Krypto Bot (Token from User Request: 8523...)
        "TELEGRAM_TOKEN_KRYPTO": "8523567139:AAGSx2MMtvMYPRWacNegsS8-5IpSaBVhXBA",
        "TELEGRAM_CHAT_ID_KRYPTO": "7675773887",
        "KRAKEN_API_KEY": "a2KLgCqIZTefZu/7NFzuyiiOC91kpLj5Jf1A0RJbOs1/BSqb+7Z/ltp/",
        "KRAKEN_SECRET": "cfQr3NQQ/Igvm/mQ0MyrMA84KMIOAG89+9aHp7oZswaUQKSXj615ThtkDDzrXvz9YjfA9rJQRctekplyHwylxg==",
        "ALPHA_VANTAGE_API_KEY": "493PNJ4J3HXW078X",
        "TRADING212_API_KEY": "31785628ZSUfgUAlnzcPtIWSXCIOFzbiLmkDC", # From .env view earlier
        # "TRADING212_API_SECRET": "NS1py4q_JdPrYQUWv7nK1TSSBl9YTvXPkyyBtlbfW8Y" # If needed
    }

    print(f"Batch installing {len(known_secrets)} known secrets...")
    for key, value in known_secrets.items():
        try:
            set_secret(key, value)
        except Exception as e:
            print(f"Skipping {key}: {e}")

    # Interactive mode for others
    # for key in keys_to_set:
    #     if key not in known_secrets:
    #         val = getpass.getpass(f"Enter value for {key}: ")
    #         if val.strip():
    #             set_secret(key, val.strip())

    print("\nKeyring population complete.")

if __name__ == "__main__":
    main()
