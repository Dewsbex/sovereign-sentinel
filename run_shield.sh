#!/bin/bash
# Load credentials
eval $(grep 'export TRADING212' ~/.bashrc | tail -2)
eval $(grep 'export TELEGRAM' ~/.bashrc | tail -2)

# Get main_bot PID
BOT_PID=$(pgrep -f "python3 main_bot.py")

if [ -z "$BOT_PID" ]; then
    echo "⚠️  Warning: main_bot.py not running. Shield will start but won't be able to kill bot."
    python3 orb_shield.py
else
    echo "✅ Found main_bot.py at PID: $BOT_PID"
    python3 orb_shield.py --bot-pid $BOT_PID
fi
