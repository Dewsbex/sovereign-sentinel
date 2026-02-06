import requests
import os
import logging

logger = logging.getLogger("ORB_Messenger")

class ORBMessenger:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.token or not self.chat_id:
            logger.warning("⚠️ Telegram credentials not found. Notifications disabled.")
            self.enabled = False
        else:
            self.enabled = True
            self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send(self, message):
        """Sends a message to Telegram."""
        if not self.enabled:
            logger.info(f"msg (local): {message}")
            return

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            requests.post(self.base_url, data=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    def notify_startup(self, equity):
        self.send(f"🚀 **Sovereign Finality ORB Engine (v32.25)**\n\n✅ System Online\n💰 Equity: £{equity:.2f}\n📡 Status: Observation Phase Started")

    def notify_shutdown(self, pnl):
        icon = "✅" if pnl >= 0 else "🔻"
        self.send(f"💤 **System Shutdown**\n\n{icon} Daily P/L: £{pnl:.2f}\n💾 State Saved.")

    def notify_trade(self, ticker, side, qty, price):
        icon = "🟢" if side == "BUY" else "🔴"
        self.send(f"{icon} **FILLED: {ticker}**\n\nSide: {side}\nQty: {qty}\nPrice: {price}")
        
    def notify_shield(self, ticker, stop, target):
        self.send(f"🛡️ **SHIELD ACTIVE: {ticker}**\n\n🛑 Stop: {stop}\n🎯 Target: {target}")

    def notify_error(self, context, error):
        self.send(f"❌ **CRITICAL ERROR**\n\nContext: {context}\nError: `{error}`")
