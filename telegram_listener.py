
import logging
import os
import json
import asyncio
from datetime import time as dtime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv

# Load Env
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
ALLOWED_USERS = []

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def load_config():
    global ALLOWED_USERS
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                data = json.load(f)
                ALLOWED_USERS = data.get('allowed_users', [])
                return data
    except Exception as e:
        print(f"Config Load Error: {e}")
        return {}

def save_config(data):
    try:
        with open('config.json', 'w') as f:
            json.dump(data, f, indent=4)
        # Reload to update global state
        load_config() 
    except Exception as e:
        print(f"Config Save Error: {e}")

async def authenticate(update: Update):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ Unauthorized Access.")
        return False
    return True

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await authenticate(update): return
    
    # Read Status from latest logs or shared state
    await update.message.reply_text("⚡ **SENTINEL STATUS**\nSystem Online.\nListening for commands...")

async def set_baserisk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await authenticate(update): return
    
    try:
        val = float(context.args[0])
        config = load_config()
        config['base_risk'] = val
        save_config(config)
        await update.message.reply_text(f"✅ Base Risk updated to {val}%")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /set_baserisk [value]")

async def panic_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await authenticate(update): return
    
    await update.message.reply_text("🚨 **PANIC SELL INITIATED**\nClosing all positions via API...")
    # Trigger logic here (file flag or API call)
    # For now, create a panic lock file that main_bot checks? 
    # Or call main_bot functionality directly (harder if separate process).
    # Spec says "The Manual Hub... /panic_sell - Immediately executes..."
    # We will invoke the close logic or set a flag.
    # Given separation, writing a PANIC file is safest for main_bot to pick up immediately?
    # Or use Trading212Client directly here.
    
    try:
        from trading212_client import Trading212Client
        client = Trading212Client()
        positions = client.get_positions()
        if positions:
            for p in positions:
                 if p.get('ticker'):
                     client.execute_order(p['ticker'], p.get('quantity'), "SELL")
            await update.message.reply_text("✅ All positions closed.")
        else:
            await update.message.reply_text("ℹ️ No open positions.")
    except Exception as e:
        await update.message.reply_text(f"❌ Panic Error: {e}")

async def heartbeat_job(context: ContextTypes.DEFAULT_TYPE):
    # Sends daily heartbeat
    for uid in ALLOWED_USERS:
        await context.bot.send_message(chat_id=uid, text="💓 System Healthy (Daily Heartbeat)")

if __name__ == '__main__':
    load_config()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('set_baserisk', set_baserisk))
    application.add_handler(CommandHandler('panic_sell', panic_sell))
    
    # Schedule Heartbeat at 08:00 UTC
    job_queue = application.job_queue
    job_queue.run_daily(heartbeat_job, time=dtime(8, 0))
    
    application.run_polling()
