from trading212_client import Trading212Client
import sys
import os
from credentials_manager import get_secret

# Add orchestrator to path to import telegram_hub
sys.path.append(r"C:\Users\steve\.gemini\antigravity\orchestrator")
try:
    from telegram_hub import hub
except ImportError:
    print("Warning: Could not import telegram_hub. Falling back to legacy method.")
    hub = None

class SovereignAlerts:
    """The Voice: Standardized Telegram notification engine."""
    
    def __init__(self, use_krypto_channel=False):
        self.client = Trading212Client()
        self.use_krypto_channel = use_krypto_channel
        
    def _format_message(self, job_ref, function_emoji, details):
        """
        Enforce Structure:
        [Project Emoji] [Function Emoji] [Project Name] | [Job Reference] | [Detailed Message]
        """
        proj_emoji = "₿" if self.use_krypto_channel else "🏛️"
        proj_name = "KRYPTO" if self.use_krypto_channel else "SOVEREIGN"
        
        # If job_ref provided, include it
        header = f"{proj_emoji} {function_emoji} **{proj_name} | Job: {job_ref}**\n\n" if job_ref else f"{proj_emoji} {function_emoji} **{proj_name}**\n\n"
        return f"{header}{details}"

    def _send(self, msg, category="STOCK"):
        """Internal routing to hub or legacy client."""
        if hub:
            if self.use_krypto_channel:
                hub.send_crypto_alert(msg)
            else:
                if category == "TRADE":
                    hub.send_stock_alert(msg)
                elif category == "HEALTH":
                    hub.send_health_update(msg)
                elif category == "BRIEF":
                    hub.send_research_brief(msg)
                else:
                    hub.send_stock_alert(msg)
        else:
            self.client.send_telegram(msg, use_krypto_channel=self.use_krypto_channel)
            
    def send_message(self, msg, category="STOCK"):
        """Send raw markdown message (assumes pre-formatted or generic)."""
        # If it's pre-formatted with emojis, just send.
        self._send(msg, category)
        
    def send_trade_alert(self, trade, event_type="ENTRY"):
        """Send formatted trade notification."""
        ticker = trade['ticker']
        qty = trade['quantity']
        price = trade.get('price', 0)
        
        func_emoji = "🚀" if event_type == "ENTRY" else "🛑"
        
        details = f"**TRADE {event_type}**\n"
        details += f"Ticker: `{ticker}`\n"
        details += f"Quantity: `{qty}`\n"
        if price:
            currency = "$" if self.use_krypto_channel else "£"
            details += f"Price: {currency}{price:,.2f}"
            
        msg = self._format_message("Target Monitor", func_emoji, details)
        self._send(msg, category="TRADE")
        
    def send_health_alert(self, job_name, status, details=""):
        """Standardized health/heartbeat alert."""
        func_emoji = "✅" if "OK" in status.upper() or "COMPLETE" in status.upper() or "OPEN" in status.upper() else "⚠️"
        if "CLOSED" in status.upper(): func_emoji = "🔴"
        if "FAIL" in status.upper() or "CRITICAL" in status.upper(): func_emoji = "🚨"

        body = f"Status: {status}\n"
        if details:
            body += f"Detail: {details}"
            
        msg = self._format_message(job_name, func_emoji, body)    
        self._send(msg, category="HEALTH")

    def send_pulse(self, targets_count, time_str):
        """Hourly system pulse."""
        details = f"Time: {time_str} UTC\nStatus: ACTIVE (Scanning)\nTargets: {targets_count} active in universe."
        msg = self._format_message("Sentinel Pulse", "💓", details)
        self._send(msg, category="HEALTH")
    
    def send_formatted_message(self, job_ref, function_emoji, title, body, category="STOCK"):
        """Send a fully formatted message complying with the 2-Emoji rule."""
        details = f"**{title}**\n\n{body}"
        msg = self._format_message(job_ref, function_emoji, details)
        self._send(msg, category)

    def send_status(self, total):
        currency = "$" if self.use_krypto_channel else "£"
        details = f"💰 Wealth: {currency}{total:,.2f}"
        msg = self._format_message("Status Update", "⚡", details)
        self._send(msg, category="STOCK")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Send Telegram Alert')
    parser.add_argument('--message', help='Message to send')
    parser.add_argument('--krypto', action='store_true', help='Use Krypto channel')
    parser.add_argument('--job', help='Job name for health alert')
    parser.add_argument('--status', help='Status for health alert')
    args = parser.parse_args()
    
    bot = SovereignAlerts(use_krypto_channel=args.krypto)
    if args.job and args.status:
        bot.send_health_alert(args.job, args.status, args.message or "")
    elif args.message:
        bot.send_message(args.message)
