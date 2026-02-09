import os, requests, base64

class Trading212Client:
    def __init__(self):
        # 1. AUTHENTICATION (37-Char Key Support)
        self.api_key = os.getenv('TRADING212_API_KEY', '').strip()
        self.api_secret = os.getenv('TRADING212_API_SECRET', '').strip()
        self.gemini_key = os.getenv('GOOGLE_API_KEY', '').strip()
        self.base_url = "https://live.trading212.com/api/v0"
        
        # 2. PERSISTENT TELEGRAM CONFIG
        self.bot_token = "8585563319:AAH0wx3peZycxqG1KC9q7FMuSwBw2ps1TGA"
        self.chat_id = "7675773887"

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
        """Used for Header Metrics"""
        res = requests.get(f"{self.base_url}/equity/account/cash", headers=self.headers)
        return self._handle_response(res)

    def get_open_orders(self):
        """Fetches all pending orders"""
        res = requests.get(f"{self.base_url}/equity/orders", headers=self.headers)
        return self._handle_response(res)

    def cancel_order(self, order_id):
        """Cancels a specific order by ID"""
        res = requests.delete(f"{self.base_url}/equity/orders/{order_id}", headers=self.headers)
        return self._handle_response(res)

    def place_limit_order(self, ticker, quantity, limit_price):
        """CRITICAL: Job C Execution Method"""
        url = f"{self.base_url}/equity/orders/limit"
        payload = {
            "ticker": f"{ticker}_US_EQ",
            "quantity": float(quantity),
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
