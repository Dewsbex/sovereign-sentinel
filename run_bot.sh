#!/bin/bash
# Load credentials
eval $(grep 'export TRADING212' ~/.bashrc | tail -2)
eval $(grep 'export TELEGRAM' ~/.bashrc | tail -2)

# Send startup notification
python3 -c "
import os
import requests
token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
if token and chat_id:
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    msg = '🚀 Sovereign Sentinel Bot STARTED\\n\\nServer: London Oracle\\nMode: Dry Run\\nWatch List: NVDA, TSLA, AMD'
    requests.post(url, json={'chat_id': chat_id, 'text': msg})
"

# Run bot
cd ~
python3 main_bot.py --tickers NVDA TSLA AMD
