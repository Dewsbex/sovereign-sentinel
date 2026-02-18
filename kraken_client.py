#!/usr/bin/env python3
"""
Kraken API Client
Simple wrapper for healthcheck and system test operations.
"""
import os
import time
import hashlib
import hmac
import base64
import urllib.parse
import requests
from dotenv import load_dotenv

load_dotenv()

class KrakenClient:
    """Minimal Kraken API client for healthcheck and testing"""
    
    def __init__(self):
        self.api_key = os.getenv('KRAKEN_API_KEY')
        self.api_secret = os.getenv('KRAKEN_SECRET')
        self.api_url = "https://api.kraken.com"
        
        if not self.api_key or not self.api_secret:
            raise ValueError("KRAKEN_API_KEY and KRAKEN_SECRET must be set in .env")
    
    def _sign(self, urlpath, data):
        """Generate Kraken API signature"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            message,
            hashlib.sha512
        )
        return base64.b64encode(signature.digest()).decode()
    
    def _request(self, endpoint, data=None, private=False):
        """Make API request to Kraken"""
        url = f"{self.api_url}{endpoint}"
        
        if private:
            if data is None:
                data = {}
            data['nonce'] = str(int(time.time() * 1000))
            
            headers = {
                'API-Key': self.api_key,
                'API-Sign': self._sign(endpoint, data)
            }
            response = requests.post(url, headers=headers, data=data, timeout=10)
        else:
            headers = {}
            response = requests.get(url, params=data, timeout=10) if data else requests.get(url, timeout=10)
        
        response.raise_for_status()
        result = response.json()
        
        if result.get('error') and len(result['error']) > 0:
            raise Exception(f"Kraken API Error: {result['error']}")
        
        return result.get('result')
    
    def get_account_balance(self):
        """Get account balances"""
        return self._request('/0/private/Balance', private=True)
    
    def get_ticker(self, pair='XXBTZUSD'):
        """Get current ticker for a pair (default: BTC/USD)"""
        result = self._request('/0/public/Ticker', data={'pair': pair})
        return result.get(pair) if result else None
    
    def get_open_orders(self):
        """Get list of open orders"""
        return self._request('/0/private/OpenOrders', private=True)
    
    def place_limit_order(self, pair, volume, price, side='buy'):
        """
        Place a limit order
        
        Args:
            pair: Trading pair (e.g., 'XXBTZUSD')
            volume: Order volume
            price: Limit price
            side: 'buy' or 'sell'
        """
        data = {
            'pair': pair,
            'type': side,
            'ordertype': 'limit',
            'price': str(price),
            'volume': str(volume),
            'validate': 'false'  # Set to 'true' for validation only
        }
        return self._request('/0/private/AddOrder', data=data, private=True)
    
    def cancel_order(self, txid):
        """Cancel an open order by transaction ID"""
        data = {'txid': txid}
        return self._request('/0/private/CancelOrder', data=data, private=True)
