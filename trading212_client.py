import os, requests, base64, json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Trading212Client:
    def __init__(self):
        # 1. AUTHENTICATION (37-Char Key Support)
        self.api_key = os.getenv('TRADING212_API_KEY')
        self.api_secret = os.getenv('TRADING212_API_SECRET')
        self.base_url = "https://live.trading212.com/api/v0"
        
        # 2. PERSISTENT TELEGRAM CONFIG
        self.bot_token = os.getenv('TELEGRAM_TOKEN', "8585563319:AAH0wx3peZycxqG1KC9q7FMuSwBw2ps1TGA")
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', "7675773887")

        # 3. HTTP BASIC AUTH (Base64 Encoded)
        if self.api_key and self.api_secret:
            auth_str = f"{self.api_key}:{self.api_secret}"
            auth_bytes = auth_str.encode('ascii')
            base64_auth = base64.b64encode(auth_bytes).decode('ascii')
            self.headers = {
                "Authorization": f"Basic {base64_auth}",
                "Content-Type": "application/json"
            }
        else:
            # Fallback (Likely to fail v2.1 spec, but prevents crash if .env missing)
            self.headers = {"Authorization": self.api_key}

        # 4. BRAIN (Gemini 2.5 Flash)
        self.gemini_key = os.getenv('GOOGLE_API_KEY', '').strip()

        # 5. INSTRUMENT CACHE (Fast Lookup)
        self.instrument_map = {}
        self.shortname_map = {}
        self._load_master_list()

    def _load_master_list(self):
        """Loads master instruments into memory for O(1) lookup"""
        try:
            if os.path.exists('data/master_instruments.json'):
                with open('data/master_instruments.json', 'r') as f:
                    data = json.load(f)
                    for item in data:
                        # Map full ticker -> item
                        self.instrument_map[item['ticker']] = item
                        
                        # Map shortName -> list of items (could be multiple, e.g. US/UK)
                        s = item.get('shortName')
                        if s:
                            if s not in self.shortname_map: self.shortname_map[s] = []
                            self.shortname_map[s].append(item)
            print(f"✅ Loaded {len(self.instrument_map)} instruments.")
        except Exception as e:
            print(f"⚠️ Failed to load master list: {e}")

    # --- SECTION A: THE TRADING HANDS ---
    def _handle_response(self, response):
        """
        Robust Response Handler (Prevents Zombies)
        Handles 401/429 HTML responses without crashing.
        """
        try:
            # Try to parse JSON
            data = response.json()
            
            if response.status_code >= 400:
                msg = data.get('message') or data.get('context') or str(data)
                return {"status": "FAILED", "error": f"{response.status_code}: {msg}"}
            return data
            
        except json.JSONDecodeError:
            # Handle non-JSON response (e.g., HTML Error Page from Cloudflare/T212)
            error_msg = f"API Error {response.status_code}: Non-JSON Response (Likely 401/429 HTML)"
            print(f"⚠️ {error_msg}")
            return {"status": "FAILED", "error": error_msg}
        except Exception as e:
            return {"status": "FAILED", "error": f"Unknown Error: {str(e)}"}

    def get_account_summary(self):
        """Used for Header Metrics (Cash specific)"""
        res = requests.get(f"{self.base_url}/equity/account/cash", headers=self.headers, timeout=10)
        return self._handle_response(res)

    def get_account_info(self):
        """Returns full account summary including investments"""
        res = requests.get(f"{self.base_url}/equity/account/summary", headers=self.headers, timeout=10)
        return self._handle_response(res)

    def get_positions(self):
        """Fetches all open positions"""
        res = requests.get(f"{self.base_url}/equity/portfolio", headers=self.headers, timeout=10)
        if hasattr(res, 'status_code') and res.status_code == 404:
             # Try alternate endpoint if portfolio fails
             res = requests.get(f"{self.base_url}/equity/positions", headers=self.headers, timeout=10)
        return self._handle_response(res)

    # Alias for compatibility with other scripts
    get_open_positions = get_positions

    def get_open_orders(self):
        """Fetches all pending orders"""
        res = requests.get(f"{self.base_url}/equity/orders", headers=self.headers, timeout=10)
        return self._handle_response(res)

    def cancel_order(self, order_id):
        """Cancels a specific order by ID"""
        res = requests.delete(f"{self.base_url}/equity/orders/{order_id}", headers=self.headers, timeout=10)
        return self._handle_response(res)

    def get_instrument_metadata(self, ticker):
        """Fetches metadata for a specific instrument"""
        try:
            res = requests.get(f"{self.base_url}/equity/metadata/instruments", headers=self.headers, timeout=10)
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

    def resolve_ticker(self, input_ticker):
        """
        Smart Ticker Resolution (Critical for SPACs & International Stocks)
        Maps inputs like 'SOFI' -> 'IPOE_US_EQ' or 'RR.L' -> 'RRl_EQ'
        """
        # 1. Exact match in master list (e.g. 'NVDA_US_EQ')
        if input_ticker in self.instrument_map:
            return input_ticker, self.instrument_map[input_ticker]
            
        # 2. Try blindly appending _US_EQ (Common case)
        us_try = f"{input_ticker}_US_EQ"
        if us_try in self.instrument_map:
            return us_try, self.instrument_map[us_try]

        # 3. Handle suffix-based logic (e.g. RR.L -> RR)
        clean_ticker = input_ticker
        is_uk = False
        if input_ticker.endswith('.L'):
            clean_ticker = input_ticker[:-2]
            is_uk = True
            
        # 4. Search by shortName
        candidates = self.shortname_map.get(clean_ticker)
        if candidates:
            # If we want UK (from .L), prefer GBX currency
            if is_uk:
                for c in candidates:
                    if c.get('currencyCode') == 'GBX':
                        return c['ticker'], c
                        
            # Default: Prefer USD/US_EQ if available, else take first
            for c in candidates:
                if 'US_EQ' in c['ticker'] or c.get('currencyCode') == 'USD':
                    return c['ticker'], c
            
            # Fallback to first candidate
            return candidates[0]['ticker'], candidates[0]
            
        # 5. Fail safe
        return None, None

    def place_limit_order(self, ticker, quantity, limit_price, side='BUY'):
        """CRITICAL: Job C Execution Method"""
        # RESOLVE TICKER (Handles SPACs, UK stocks, etc.)
        real_ticker, inst_data = self.resolve_ticker(ticker)
        
        if not real_ticker:
            print(f"⛔ Order Blocked: '{ticker}' not found in Master List (Logic Failed).")
            return {"status": "FAILED", "error": "Invalid Ticker Resolution"}
            
        # Verify min trade quantity if available
        min_qty = inst_data.get('minTradeQuantity', 0) if inst_data else 0
        if quantity < min_qty:
             print(f"⚠️ Adjusted Qty {quantity} -> {min_qty} (Min Trade Size)")
             quantity = min_qty

        url = f"{self.base_url}/equity/orders/limit"
        
        # Adjust quantity sign based on side if needed
        qty = float(quantity)
        if side.upper() == 'SELL' and qty > 0:
            qty = -qty
            
        payload = {
            "ticker": real_ticker,
            "quantity": qty,
            "limitPrice": float(limit_price),
            "timeValidity": "GOOD_TILL_CANCEL"
        }
        res = requests.post(url, json=payload, headers=self.headers)
        return self._handle_response(res)

    def execute_order(self, ticker, quantity, side='BUY'):
        """
        Unified Execution: Executes order immediately.
        Uses a slightly aggressive limit to ensure fill (simulated market order).
        """
        # Fetch current price to set limit
        try:
            ticker_obj = __import__('yfinance').Ticker(ticker)
            price = ticker_obj.fast_info['last_price']
            
            # Add 0.5% buffer to ensure fill
            if side.upper() == 'BUY':
                limit_price = price * 1.005
            else:
                limit_price = price * 0.995
                
            return self.place_limit_order(ticker, quantity, limit_price, side)
        except Exception as e:
            print(f"❌ Execution failed for {ticker}: {e}")
            return {"status": "FAILED", "error": str(e)}

    # --- SECTION B: THE GROUNDED BRAIN (New 2026 AI) ---
    def gemini_query(self, prompt):
        # Using Gemini 2.0 Pro (Experimental 02-05) for APROMS A-Tier reasoning
        # FALLBACK: If Pro fails (experimental), fall back to Flash
        models = [
            "gemini-2.0-pro-exp-02-05",
            "gemini-2.5-flash"
        ]
        
        last_error = ""
        
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
            
            # Grounding with Google Search tool block
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "tools": [{"google_search": {}}]
            }
            
            try:
                res = requests.post(url, json=payload)
                if res.status_code != 200:
                    last_error = f"Model {model} Error ({res.status_code}): {res.json().get('error', {}).get('message', 'Unknown')}"
                    continue # Try next model
                
                data = res.json()
                candidates = data.get('candidates', [])
                if not candidates:
                    last_error = f"Model {model} Error: No candidates."
                    continue
                    
                # Success
                return candidates[0]['content']['parts'][0]['text']
                
            except Exception as e:
                last_error = f"System Error ({model}): {e}"
                continue
                
        return f"Gemini All Models Failed. Last Error: {last_error}"

    def send_telegram(self, message):
        """Sends message to Telegram, splitting if > 4096 chars"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        # Split into chunks of 4000 to be safe (limit is 4096)
        chunk_size = 4000
        
        for i in range(0, len(message), chunk_size):
            chunk = message[i:i+chunk_size]
            try:
                res = requests.post(url, data={"chat_id": self.chat_id, "text": chunk, "parse_mode": "Markdown"})
                if res.status_code != 200:
                    # Fallback: Try without Markdown if parsing fails (common with special chars)
                    requests.post(url, data={"chat_id": self.chat_id, "text": chunk})
            except Exception as e:
                print(f"⚠️ Telegram Send Error: {e}")

    # --- SECTION C: DATA INTEGRITY (Neon Sentry) ---
    def sync_master_list(self):
        """
        Fetches the full 10,000+ instrument list from Trading 212
        and saves it to data/master_instruments.json
        """
        print("🔄 Syncing Master Instrument List...")
        try:
            # Note: The v0 API endpoint for all instruments is /equity/metadata/instruments
            res = requests.get(f"{self.base_url}/equity/metadata/instruments", headers=self.headers)
            
            if res.status_code != 200:
                print(f"❌ API Error {res.status_code}: {res.text[:200]}")
            
            instruments = self._handle_response(res)
            
            if isinstance(instruments, list):
                os.makedirs('data', exist_ok=True)
                with open('data/master_instruments.json', 'w') as f:
                    json.dump(instruments, f)
                print(f"✅ Sync Complete. {len(instruments)} instruments cached.")
                return True
            else:
                print(f"❌ Sync Failed: Invalid response format. {instruments}")
                return False
        except Exception as e:
            print(f"❌ Sync Error: {e}")
            return False

    def validate_ticker(self, ticker):
        """
        Validates if a ticker exists in the local Master List.
        Returns the instrument object if found, else None.
        """
        try:
            with open('data/master_instruments.json', 'r') as f:
                instruments = json.load(f)
            
            for inst in instruments:
                if inst.get('ticker') == ticker:
                    return inst
            return None
        except FileNotFoundError:
            print("⚠️ Master List not found. Run sync_master_list() first.")
            return None
        except Exception as e:
            print(f"⚠️ Validation Error: {e}")
            return None
