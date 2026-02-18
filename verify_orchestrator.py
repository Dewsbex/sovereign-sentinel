from orchestrator_config import load_master_env, get_secret
import requests

def main():
    print("Verifying Sovereign-Sentinel Orchestrator Integration...")
    
    if not load_master_env():
        print("FAIL: Could not load master env.")
        return

    # Check Trading 212 Key
    key = get_secret("TRADING212_API_KEY")
    if key:
        print(f"PASS: Trading 212 Key found (starts with {key[:4]}...)")
    else:
        print("FAIL: Trading 212 Key missing")

    # Check Telegram
    token = get_secret("TELEGRAM_TOKEN_SENTINEL")
    chat_id = get_secret("TELEGRAM_CHAT_ID_SENTINEL")
    
    if token and chat_id:
        print(f"PASS: Telegram Config found (Chat ID: {chat_id})")
        # Try a quick ping
        url = f"https://api.telegram.org/bot{token}/getMe"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                user = resp.json().get('result', {}).get('username', 'Unknown')
                print(f"PASS: Telegram Bot API Reached (@{user})")
            else:
                print(f"FAIL: Telegram API Error {resp.status_code}")
        except Exception as e:
            print(f"FAIL: Telegram Connection Error {e}")
    else:
        print("FAIL: Telegram Config missing")

if __name__ == "__main__":
    main()
