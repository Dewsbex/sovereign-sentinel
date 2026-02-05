import os
import requests

print("--- KEY VERIFICATION ---")
token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not token:
    print("❌ TELEGRAM_TOKEN is missing")
else:
    print(f"✅ TELEGRAM_TOKEN found (len={len(token)})")

if not chat_id:
    print("❌ TELEGRAM_CHAT_ID is missing")
else:
    print(f"✅ TELEGRAM_CHAT_ID found (len={len(chat_id)})")

if token and chat_id:
    print("Attempting raw message...")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={'chat_id': chat_id, 'text': '🔑 Key Verification Success'})
    print(f"Response: {resp.status_code} {resp.text}")
print("--- END ---")
