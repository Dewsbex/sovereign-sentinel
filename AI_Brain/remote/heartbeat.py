import time
import datetime
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class HeartbeatService:
    """
    Telegram control service heartbeat function.
    Transmits a 'System Healthy' status message every 24 hours at 08:00 UTC.
    """

    def __init__(self):
        self.running = False
        self.target_hour = 8 # 08:00 UTC
        self.target_minute = 0
        # Prioritize Krypto-Specific Bot, fallback to General
        self.bot_token = os.getenv("TELEGRAM_TOKEN_KRYPTO") or os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID_KRYPTO") or os.getenv("TELEGRAM_CHAT_ID") 

    def start(self):
        self.running = True
        print("Heartbeat Service Started.")
        self._loop()

    def stop(self):
        self.running = False
        print("Heartbeat Service Stopped.")

    def _loop(self):
        while self.running:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            
            if now_utc.hour == self.target_hour and now_utc.minute == self.target_minute:
                self.send_heartbeat()
                time.sleep(61)
            else:
                 time.sleep(10)

    def send_heartbeat(self):
        """
        Transmits the heartbeat message via Telegram API.
        """
        message = "System Healthy"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        # Prefix with 'Krypto' as requested to distinguish from ISA
        full_message = f"Krypto: [{timestamp}] Heartbeat: {message}"
        print(full_message)

        if self.bot_token and self.chat_id:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {"chat_id": self.chat_id, "text": full_message}
            try:
                response = requests.post(url, data=data, timeout=10)
                if response.status_code == 200:
                    print("Telegram message sent successfully.")
                else:
                    print(f"Failed to send Telegram message: {response.text}")
            except Exception as e:
                print(f"Error sending Telegram message: {e}")
        else:
            print("Telegram credentials not found (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID). Message logged only.")

def main():
    service = HeartbeatService()
    print("Initializing Heartbeat Service...")
    
    # Test sending immediately
    service.send_heartbeat()

if __name__ == "__main__":
    main()
