import os, requests, base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Trading212Client:
    def __init__(self):
        # 1. AUTHENTICATION (37-Char Key Support)
        self.api_key = os.getenv('TRADING212_API_KEY', '').strip()
        self.api_secret = os.getenv('TRADING212_API_SECRET', '').strip()
        self.gemini_key = os.getenv('GOOGLE_API_KEY', '').strip()
        self.base_url = "https://live.trading212.com/api/v0"
        
        # 2. PERSISTENT TELEGRAM CONFIG
        self.bot_token = os.getenv('TELEGRAM_TOKEN', "8585563319:AAH0wx3peZycxqG1KC9q7FMuSwBw2ps1TGA")
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', "7675773887")

        if self.api_key and self.api_secret:
            creds = f"{self.api_key}:{self.api_secret}"
            encoded = base64.b64encode(creds.encode('utf-8')).decode('utf-8')
            self.headers = {"Authorization": f"Basic {encoded}"}
        else:
            self.headers = {}

    # --- SECTION A: THE TRADING HANDS (Restored) ---
    def _handle_response(self, response):
        try:
            data = response.json()
            if response.status_code >= 400:
                msg = data.get('message') or data.get('context') or str(data)
                return {"status": "FAILED", "error": f"{response.status_code}: {msg}"}
            return data
        except:
            if response.status_code == 200: return {"status": "OK"}
            return {"status": "FAILED", "error": f"HTTP {response.status_code}"}

    def get_account_summary(self):
        """Used for Header Metrics (Cash specific)"""
        res = requests.get(f"{self.base_url}/equity/account/cash", headers=self.headers)
        return self._handle_response(res)

    def get_account_info(self):
        """Returns full account summary including investments"""
        res = requests.get(f"{self.base_url}/equity/account/summary", headers=self.headers)
        return self._handle_response(res)

    def get_positions(self):
        """Fetches all open positions"""
        res = requests.get(f"{self.base_url}/equity/portfolio", headers=self.headers)
        if hasattr(res, 'status_code') and res.status_code == 404:
             # Try alternate endpoint if portfolio fails (some versions use positions)
             res = requests.get(f"{self.base_url}/equity/positions", headers=self.headers)
        return self._handle_response(res)

    # Alias for compatibility with other scripts
    get_open_positions = get_positions

    def get_open_orders(self):
        """Fetches all pending orders"""
        res = requests.get(f"{self.base_url}/equity/orders", headers=self.headers)
        return self._handle_response(res)

    def cancel_order(self, order_id):
        """Cancels a specific order by ID"""
        res = requests.delete(f"{self.base_url}/equity/orders/{order_id}", headers=self.headers)
        return self._handle_response(res)

    def get_instrument_metadata(self, ticker):
        """Fetches metadata for a specific instrument"""
        # Note: API doesn't have a single-ticker metadata endpoint in v0, 
        # usually we traverse the list, but for specific check:
        # We can implement a filter loop or return None if not easily available.
        # However, looking at test_trading212.py, it expects this.
        # Efficient way: Use /equity/metadata/instruments and filter locally (heavy)
        # Or just mocking/skipping.
        # Let's implement a 'light' version or fetch all (cache in future)
        # For now, simplistic implementation:
        try:
            res = requests.get(f"{self.base_url}/equity/metadata/instruments", headers=self.headers)
            data = self._handle_response(res)
            if isinstance(data, list):
                for item in data:
                    if item.get('ticker') == ticker:
                        return item
            return {}
        except:
            return {}

    def calculate_max_buy(self, ticker, cash, price):
        """Helper to calculate max shares affordable"""
        if price <= 0: return 0
        return int(cash / price)

    def place_limit_order(self, ticker, quantity, limit_price, side='BUY'):
        """CRITICAL: Job C Execution Method"""
        url = f"{self.base_url}/equity/orders/limit"
        
        # Adjust quantity sign based on side if needed, or rely on caller
        # API requires negative quantity for SELL
        qty = float(quantity)
        if side.upper() == 'SELL' and qty > 0:
            qty = -qty
            
        payload = {
            "ticker": f"{ticker}_US_EQ",
            "quantity": qty,
            "limitPrice": float(limit_price),
            "timeValidity": "GOOD_TILL_CANCEL"
        }
        res = requests.post(url, json=payload, headers=self.headers)
        return self._handle_response(res)

    # --- SECTION B: THE GROUNDED BRAIN (New 2026 AI) ---
    def gemini_query(self, prompt):
        # Using Gemini 2.5 Flash for Tier 1 Quota stability
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_key}"
        
        # Grounding with Google Search tool block
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}]
        }
        
        try:
            res = requests.post(url, json=payload)
            data = res.json()
            if res.status_code != 200:
                return f"Gemini API Error ({res.status_code}): {data.get('error', {}).get('message', 'Unknown Error')}"
            
            candidates = data.get('candidates', [])
            if not candidates:
                return "Gemini Error: No response candidates returned."
                
            return candidates[0]['content']['parts'][0]['text']
        except Exception as e:
            return f"System Error: {e}"

    def send_telegram(self, message):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        requests.post(url, data={"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"})
