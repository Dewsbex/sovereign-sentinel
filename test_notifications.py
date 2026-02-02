import os
import requests

# Test notification script to verify GitHub Secrets are working

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

print("=== Testing GitHub Secrets ===")
print(f"DISCORD_WEBHOOK_URL: {'SET ✅' if DISCORD_WEBHOOK_URL else 'NOT SET ❌'}")
print(f"TELEGRAM_TOKEN: {'SET ✅' if TELEGRAM_TOKEN else 'NOT SET ❌'}")
print(f"TELEGRAM_CHAT_ID: {'SET ✅' if TELEGRAM_CHAT_ID else 'NOT SET ❌'}")

# Test Discord
if DISCORD_WEBHOOK_URL:
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": "🧪 **TEST**: Discord notification working from GitHub Actions!"})
        if response.status_code == 204:
            print("✅ Discord notification sent successfully")
        else:
            print(f"❌ Discord failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Discord error: {e}")
else:
    print("⚠️ Skipping Discord test (webhook not set)")

# Test Telegram
if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        response = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': '🧪 TEST: Telegram notification working from GitHub Actions!',
            'parse_mode': 'HTML'
        })
        if response.status_code == 200:
            print("✅ Telegram notification sent successfully")
        else:
            print(f"❌ Telegram failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")
else:
    print("⚠️ Skipping Telegram test (credentials not set)")
