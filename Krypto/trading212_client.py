import os, requests, base64, json, time
from credentials_manager import get_secret

class Trading212Client:
    def __init__(self):
        # 1. AUTHENTICATION (37-Char Key Support)
        self.api_key = get_secret('TRADING212_API_KEY')
        self.api_secret = get_secret('TRADING212_API_SECRET')
        self.base_url = "https://live.trading212.com/api/v0"
        
        # 2. PERSISTENT TELEGRAM CONFIG
        self.bot_token = get_secret('TELEGRAM_TOKEN') or "8585563319:AAH0wx3peZycxqG1KC9q7FMuSwBw2ps1TGA"
        self.chat_id = get_secret('TELEGRAM_CHAT_ID') or "7675773887"

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
        self.gemini_key = get_secret('GOOGLE_API_KEY')

        # 5. INSTRUMENT CACHE (Fast Lookup)
        self.instrument_map = {}
        self.shortname_map = {}
        self._load_master_list()

    def load_balance_state(self):
        """Compatibility stub: Auditor handles this, but client allows call for P&L tracking."""
        return {"realized_profit": 0.0, "timestamp": time.time()}

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
            print(f"Loaded {len(self.instrument_map)} instruments.")
        except Exception as e:
            print(f"Failed to load master list: {e}")

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
            print(f"{error_msg}")
            return {"status": "FAILED", "error": error_msg}
        except Exception as e:
            return {"status": "FAILED", "error": f"Unknown Error: {str(e)}"}

    def _make_request(self, method, url, **kwargs):
        """Internal method to handle rate limits and retries."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    res = requests.get(url, headers=self.headers, timeout=10, **kwargs)
                elif method.upper() == 'POST':
                    res = requests.post(url, headers=self.headers, timeout=10, **kwargs)
                elif method.upper() == 'DELETE':
                    res = requests.delete(url, headers=self.headers, timeout=10, **kwargs)
                else:
                    return {"status": "FAILED", "error": f"Unsupported method: {method}"}
                
                if res.status_code == 429:
                    reset_time = res.headers.get('x-ratelimit-reset')
                    if reset_time:
                        try:
                            wait_sec = max(int(reset_time) - int(time.time()), 1)
                            print(f"Rate limited (429). Waiting {wait_sec}s until reset...")
                            time.sleep(wait_sec + 1)
                            continue
                        except:
                            time.sleep(5)
                            continue
                    else:
                        time.sleep(5)
                        continue
                        
                return self._handle_response(res)
            except Exception as e:
                print(f"Request Error {method} {url}: {e}")
                time.sleep(2)
                continue
        return {"status": "FAILED", "error": f"Max retries reached for {url}"}

    def _paginate_request(self, url):
        """Handles cursor-based pagination continuously"""
        all_items = []
        domain = self.base_url.replace("/api/v0", "")
        current_url = url
        
        while current_url:
            data = self._make_request('GET', current_url)
            
            if isinstance(data, dict) and data.get("status") == "FAILED":
                if not all_items: return data
                break
                
            if isinstance(data, list):
                all_items.extend(data)
                break
            elif isinstance(data, dict):
                if 'items' in data:
                    all_items.extend(data['items'])
                
                next_path = data.get('nextPagePath')
                if next_path:
                    current_url = f"{domain}{next_path}"
                else:
                    current_url = None
            else:
                break
                
        return all_items

    def get_account_summary(self):
        """Used for Header Metrics (Cash specific)"""
        return self._make_request('GET', f"{self.base_url}/equity/account/cash")

    def get_account_info(self):
        """Returns full account summary including investments"""
        return self._make_request('GET', f"{self.base_url}/equity/account/summary")

    def get_positions(self):
        """Fetches all open positions (Paginated via /positions)"""
        return self._paginate_request(f"{self.base_url}/equity/positions")

    # Alias for compatibility with other scripts
    get_open_positions = get_positions

    def get_open_orders(self):
        """Fetches all pending orders (Paginated)"""
        return self._paginate_request(f"{self.base_url}/equity/orders")

    def cancel_order(self, order_id):
        """Cancels a specific order by ID"""
        return self._make_request('DELETE', f"{self.base_url}/equity/orders/{order_id}")

    def get_instrument_metadata(self, ticker):
        """Fetches metadata for a specific instrument"""
        try:
            data = self._make_request('GET', f"{self.base_url}/equity/metadata/instruments")
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
            candidate = self.instrument_map[input_ticker]
            return input_ticker, candidate.get('shortName', input_ticker.split('_')[0]), candidate
            
        # 2. Try blindly appending _US_EQ (Common case)
        us_try = f"{input_ticker}_US_EQ"
        if us_try in self.instrument_map:
            candidate = self.instrument_map[us_try]
            return us_try, candidate.get('shortName', input_ticker), candidate

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
                        return c['ticker'], f"{c.get('shortName', clean_ticker)}.L", c
                        
            # Default: Prefer USD/US_EQ if available, else take first
            for c in candidates:
                if 'US_EQ' in c['ticker'] or c.get('currencyCode') == 'USD':
                    return c['ticker'], c.get('shortName', clean_ticker), c
            
            # Fallback to first candidate
            return candidates[0]['ticker'], candidates[0].get('shortName', clean_ticker), candidates[0]
            
        # 5. Fail safe
        return None, None, None

    def place_limit_order(self, ticker, quantity, limit_price, side='BUY'):
        """CRITICAL: Job C Execution Method"""
        # RESOLVE TICKER (Handles SPACs, UK stocks, etc.)
        real_ticker, yf_ticker, inst_data = self.resolve_ticker(ticker)
        
        if not real_ticker:
            print(f"Order Blocked: '{ticker}' not found in Master List (Logic Failed).")
            return {"status": "FAILED", "error": "Invalid Ticker Resolution"}
            
        # Verify min trade quantity if available
        min_qty = inst_data.get('minTradeQuantity', 0) if inst_data else 0
        if quantity < min_qty:
             print(f"Adjusted Qty {quantity} -> {min_qty} (Min Trade Size)")
             quantity = min_qty

        # Adjust quantity sign based on side if needed
        qty = float(quantity)
        if side.upper() == 'SELL' and qty > 0:
            qty = -qty

        # Idempotency Guard: Check if an identical open order already exists
        open_orders = self.get_open_orders()
        if isinstance(open_orders, list):
            for order in open_orders:
                if order.get('ticker') == real_ticker and order.get('quantity') == qty:
                    existing_price = order.get('limitPrice')
                    if existing_price and abs(float(existing_price) - float(limit_price)) / float(limit_price) < 0.01:
                        print(f"Idempotency Guard: Identical order already pending for {real_ticker}. Blocking duplicate.")
                        return {"status": "FAILED", "error": "Duplicate Order Blocked (Idempotency)"}

        url = f"{self.base_url}/equity/orders/limit"
        
        payload = {
            "ticker": real_ticker,
            "quantity": qty,
            "limitPrice": float(limit_price),
            "timeValidity": "GOOD_TILL_CANCEL"
        }
        return self._make_request('POST', url, json=payload)

    def place_market_order(self, ticker, quantity, side='BUY', extended_hours=True):
        """CRITICAL: Job D (Antigravity) Execution Method"""
        real_ticker, yf_ticker, inst_data = self.resolve_ticker(ticker)
        
        if not real_ticker:
            print(f"Market Order Blocked: '{ticker}' not found in Master List (Logic Failed).")
            return {"status": "FAILED", "error": "Invalid Ticker Resolution"}
            
        # Verify min trade quantity if available
        min_qty = inst_data.get('minTradeQuantity', 0) if inst_data else 0
        if quantity < min_qty:
             print(f"Adjusted Qty {quantity} -> {min_qty} (Min Trade Size)")
             quantity = min_qty

        # Adjust quantity sign based on side if needed
        qty = float(quantity)
        if side.upper() == 'SELL' and qty > 0:
            qty = -qty

        url = f"{self.base_url}/equity/orders/market"
        
        payload = {
            "ticker": real_ticker,
            "quantity": qty,
            "extendedHours": extended_hours
        }
        return self._make_request('POST', url, json=payload)

    def place_stop_order(self, ticker, quantity, stop_price, side='SELL', time_validity='GOOD_TILL_CANCEL'):
        """CRITICAL: Job D (Antigravity) Execution Method"""
        real_ticker, yf_ticker, inst_data = self.resolve_ticker(ticker)
        
        if not real_ticker:
            print(f"Stop Order Blocked: '{ticker}' not found in Master List (Logic Failed).")
            return {"status": "FAILED", "error": "Invalid Ticker Resolution"}
            
        # Verify min trade quantity if available
        min_qty = inst_data.get('minTradeQuantity', 0) if inst_data else 0
        if abs(quantity) < min_qty:
             print(f"Adjusted Qty {quantity} -> {min_qty} (Min Trade Size)")
             quantity = min_qty

        # Adjust quantity sign based on side if needed
        qty = float(quantity)
        if side.upper() == 'SELL' and qty > 0:
            qty = -qty
            
        url = f"{self.base_url}/equity/orders/stop"
        
        payload = {
            "ticker": real_ticker,
            "quantity": qty,
            "stopPrice": float(stop_price),
            "timeValidity": time_validity
        }
        return self._make_request('POST', url, json=payload)

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
            print(f"Execution failed for {ticker}: {e}")
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

    def send_telegram(self, message, use_krypto_channel=False):
        """Sends message to Telegram, splitting if > 4096 chars"""
        # Select channel based on flag
        if use_krypto_channel:
            bot_token = get_secret('TELEGRAM_TOKEN_KRYPTO') or self.bot_token
            chat_id = get_secret('TELEGRAM_CHAT_ID_KRYPTO') or self.chat_id
        else:
            bot_token = self.bot_token
            chat_id = self.chat_id
            
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Split into chunks of 4000 to be safe (limit is 4096)
        chunk_size = 4000
        
        for i in range(0, len(message), chunk_size):
            chunk = message[i:i+chunk_size]
            try:
                res = requests.post(url, data={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"})
                if res.status_code != 200:
                    # Fallback: Try without Markdown if parsing fails (common with special chars)
                    requests.post(url, data={"chat_id": chat_id, "text": chunk})
            except Exception as e:
                print(f"Telegram Send Error: {e}")

    def send_voice(self, audio_path, caption=None, use_krypto_channel=False):
        """Send audio file as voice message."""
        if use_krypto_channel:
            bot_token = get_secret('TELEGRAM_TOKEN_KRYPTO') or self.bot_token
            chat_id = get_secret('TELEGRAM_CHAT_ID_KRYPTO') or self.chat_id
        else:
            bot_token = self.bot_token
            chat_id = self.chat_id

        url = f"https://api.telegram.org/bot{bot_token}/sendVoice"
        
        try:
            with open(audio_path, 'rb') as audio:
                files = {'voice': audio}
                data = {'chat_id': chat_id}
                if caption:
                    data['caption'] = caption
                res = requests.post(url, data=data, files=files)
                if res.status_code != 200:
                    print(f"Telegram Voice Error: {res.text}")
                    return False
            return True
        except Exception as e:
            print(f"Telegram Send Voice Error: {e}")
            return False

    # --- SECTION C: DATA INTEGRITY (Neon Sentry) ---
    def sync_master_list(self):
        """
        Fetches the full 10,000+ instrument list from Trading 212
        and saves it to data/master_instruments.json
        """
        print("🔄 Syncing Master Instrument List...")
        try:
            # Note: The v0 API endpoint for all instruments is /equity/metadata/instruments
            instruments = self._make_request('GET', f"{self.base_url}/equity/metadata/instruments")
            
            if isinstance(instruments, list):
                # Filter out suspended/delisted instruments
                active_instruments = [inst for inst in instruments if str(inst.get('workingScheduleId', '')) != '0']
                
                os.makedirs('data', exist_ok=True)
                with open('data/master_instruments.json', 'w') as f:
                    json.dump(active_instruments, f)
                print(f"Sync Complete. {len(active_instruments)} active instruments cached (out of {len(instruments)} total).")
                return True
            else:
                print(f"Sync Failed: Invalid response format. {instruments}")
                return False
        except Exception as e:
            print(f"Sync Error: {e}")
            return False

    def validate_ticker(self, ticker):
        """
        Validates if a ticker exists in the local Master List.
        Returns the instrument object if found, else None.
        """
        if not self.instrument_map:
            self._load_master_list()
            
        real_ticker, yf_ticker, inst_data = self.resolve_ticker(ticker)
        if real_ticker:
            return inst_data
        return None


if __name__ == "__main__":
    import argparse
    from audit_log import AuditLogger
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--sync', action='store_true', help='Sync Master Instrument List')
    args = parser.parse_args()
    
    if args.sync:
        logger = AuditLogger("SS011-DataSync")
        logger.log("JOB_START", "System", "Starting Master List Sync")
        
        try:
            client = Trading212Client()
            success = client.sync_master_list()
            
            if success:
                logger.log("JOB_COMPLETE", "System", "Sync Successful", "SUCCESS")
                client.send_telegram("✅ **Data Sync Complete**\nTrading 212 Product list has been successfully cached and is ready for tomorrow's trading session!")
            else:
                logger.log("JOB_FAILURE", "System", "Sync Failed", "ERROR")
                
        except Exception as e:
            logger.log("JOB_ERROR", "System", str(e), "ERROR")
            print(f"Sync Error: {e}")
