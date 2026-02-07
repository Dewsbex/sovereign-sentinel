"""
Trading 212 API Client
Handles authentication, position tracking, and order execution.
"""

import os
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime

# API Configuration
API_KEY = os.getenv('TRADING212_API_KEY')
BASE_URL = 'https://live.trading212.com'

class Trading212Client:
    """Client for Trading 212 Equity API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or API_KEY
        self.base_url = BASE_URL
        self.headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        
        if not self.api_key:
            raise ValueError("Trading 212 API key not found. Set TRADING212_API_KEY environment variable.")
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, retry_count: int = 3) -> Dict:
        """
        Make authenticated API request with exponential backoff retry logic.
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retry_count):
            try:
                if method == 'GET':
                    response = requests.get(url, headers=self.headers, timeout=10)
                elif method == 'POST':
                    response = requests.post(url, headers=self.headers, json=data, timeout=10)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2 ** attempt))
                    print(f"⚠️  Rate limited. Retrying after {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                # Handle authentication errors
                if response.status_code == 401:
                    raise Exception("Authentication failed. Check API key.")
                
                # Raise for other HTTP errors
                response.raise_for_status()
                
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt == retry_count - 1:
                    raise Exception(f"Request timed out after {retry_count} attempts")
                time.sleep(2 ** attempt)
            
            except requests.exceptions.RequestException as e:
                if attempt == retry_count - 1:
                    raise Exception(f"API request failed: {str(e)}")
                time.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    def get_positions(self) -> List[Dict]:
        """
        Fetch all open positions.
        Returns: List of position objects with P/L and quantity data.
        """
        return self._request('GET', '/api/v0/equity/positions')
    
    def get_instrument_metadata(self, ticker: str) -> Dict:
        """
        Get instrument metadata including trading limits and exchange info.
        """
        instruments = self._request('GET', '/api/v0/equity/metadata/instruments')
        
        for instrument in instruments:
            if instrument['ticker'] == ticker:
                return instrument
        
        raise ValueError(f"Instrument not found: {ticker}")
    
    def place_limit_order(self, ticker: str, quantity: float, limit_price: float, side: str = 'BUY') -> Dict:
        """
        Place a limit order.
        
        Args:
            ticker: Instrument ticker (e.g., 'AAPL_US_EQ')
            quantity: Number of shares (supports fractional)
            limit_price: Limit price per share
            side: 'BUY' or 'SELL'
        
        Returns:
            Order confirmation with order ID
        """
        payload = {
            'ticker': ticker,
            'quantity': quantity,
            'limitPrice': limit_price,
            'side': side,
            'type': 'LIMIT',
            'timeValidity': 'DAY'
        }
        
        return self._request('POST', '/api/v0/equity/orders', data=payload)
    
    def get_order_status(self, order_id: int) -> Dict:
        """
        Check the status of a specific order.
        """
        return self._request('GET', f'/api/v0/equity/orders/{order_id}')
    
    def calculate_max_buy(self, ticker: str, available_cash: float, current_price: float) -> float:
        """
        Calculate maximum quantity that can be purchased.
        
        Args:
            ticker: Instrument ticker
            available_cash: Available cash in account
            current_price: Current market price
        
        Returns:
            Maximum affordable quantity (rounded to min trade quantity)
        """
        try:
            metadata = self.get_instrument_metadata(ticker)
            min_quantity = metadata['minTradeQuantity']
            
            # Calculate max affordable shares
            max_shares = available_cash / current_price
            
            # Round down to nearest min trade quantity
            max_shares = (max_shares // min_quantity) * min_quantity
            
            return max_shares
            
        except Exception as e:
            print(f"⚠️  Error calculating max buy: {e}")
            return 0.0


def test_connection():
    """Test API connection and authentication"""
    try:
        client = Trading212Client()
        positions = client.get_positions()
        print(f"✅ Connected successfully. Retrieved {len(positions)} positions.")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == '__main__':
    # Run connection test
    test_connection()
