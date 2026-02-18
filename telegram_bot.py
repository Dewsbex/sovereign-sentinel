from trading212_client import Trading212Client
import sys
import os

# Add orchestrator to path to import telegram_hub
sys.path.append(r"C:\Users\steve\.gemini\antigravity\orchestrator")
try:
    from telegram_hub import hub
except ImportError:
    print("Warning: Could not import telegram_hub. Falling back to legacy method.")
    hub = None

class SovereignAlerts:
    """The Voice: Telegram notification engine with fixed currency formatting."""
    
    def __init__(self, use_krypto_channel=False):
        self.client = Trading212Client()
        self.use_krypto_channel = use_krypto_channel
        
    def send_message(self, msg):
        """Send raw markdown message"""
        if hub:
            if self.use_krypto_channel:
                hub.send_crypto_alert(msg)
            else:
                hub.send_stock_alert(msg)
        else:
            # Fallback to legacy client method if hub fails
            self.client.send_telegram(msg, use_krypto_channel=self.use_krypto_channel)
        
    def send_trade_alert(self, trade, event_type="ENTRY"):
        """Send formatted trade notification"""
        ticker = trade['ticker']
        qty = trade['quantity']
        price = trade.get('price', 0)
        
        emoji = "🚀" if event_type == "ENTRY" else "🛑"
        msg = f"{emoji} **TRADE {event_type}**\n"
        msg += f"Ticker: `{ticker}`\n"
        msg += f"Quantity: `{qty}`\n"
        if price:
            msg += f"Price: £{price:,.2f}"
            
        self.send_message(msg)
        
    def send_status(self, total):
        msg = f"⚡ **SENTINEL STATUS** ⚡\n💰 Wealth: £{total:,.2f}"
        self.send_message(msg)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Send Telegram Alert')
    parser.add_argument('--message', required=True, help='Message to send')
    parser.add_argument('--krypto', action='store_true', help='Use Krypto channel')
    args = parser.parse_args()
    
    bot = SovereignAlerts(use_krypto_channel=args.krypto)
    bot.send_message(args.message)
