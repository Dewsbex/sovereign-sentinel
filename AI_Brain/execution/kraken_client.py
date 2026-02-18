import time
import requests
import base64
import hashlib
import hmac
import os
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KrakenClient:
    """
    Client for interacting with Kraken API.
    Implements secure request signing and basic order management.
    """
    def __init__(self, api_key=None, api_secret=None):
        self.api_url = "https://api.kraken.com"
        self.api_key = api_key or os.getenv("KRAKEN_API_KEY")
        self.api_secret = api_secret or os.getenv("KRAKEN_SECRET")
        self.session = requests.Session()
        
    def _get_signature(self, urlpath, data, secret):
        postdata = urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()

    def _request(self, method, uri, timeout=10, data=None):
        if data is None:
            data = {}
        
        url = self.api_url + uri
        
        headers = {
            'User-Agent': 'Sovereign-Sentinel/1.0',
            'API-Key': self.api_key,
        }
        
        if method in ['POST', 'PUT', 'DELETE']:
            data['nonce'] = str(int(time.time() * 1000))
            headers['API-Sign'] = self._get_signature(uri, data, self.api_secret)
        
        response = self.session.request(method, url, headers=headers, data=data, timeout=timeout)
        
        if response.status_code not in [200, 201, 202]:
            print(f"Kraken API Error: {response.status_code} - {response.text}")
            return None
            
        json_resp = response.json()
        if json_resp.get('error'):
            print(f"Kraken API Error in Response: {json_resp['error']}")
            return None
            
        return json_resp.get('result')

    def get_server_time(self):
        return self._request('GET', '/0/public/Time')

    def get_account_balance(self):
        return self._request('POST', '/0/private/Balance')

    def get_trade_balance(self, asset="ZUSD"):
        params = {"asset": asset}
        return self._request('POST', '/0/private/TradeBalance', data=params)

    def get_open_orders(self):
        return self._request('POST', '/0/private/OpenOrders')

    def add_order(self, pair, type, side, volume, price=None, leverage=None):
        data = {
            "pair": pair,
            "type": type,
            "ordertype": "limit" if price else "market",
            "volume": str(volume),
            "leverage": "none" if not leverage else str(leverage)
        }
        if price:
            data["price"] = str(price)
            
        return self._request('POST', '/0/private/AddOrder', data=data)

    def cancel_order(self, txid):
        data = {"txid": txid}
        return self._request('POST', '/0/private/CancelOrder', data=data)

# Test Stub
if __name__ == "__main__":
    client = KrakenClient()
    # print(client.get_server_time()) 
