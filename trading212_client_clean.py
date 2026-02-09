import base64
import os
import requests
from typing import Dict, Optional

class Trading212Client:
    def __init__(self):
        self.key_id = os.getenv('TRADING212_API_KEY')
        self.secret = os.getenv('TRADING212_API_SECRET')
        self.base_url = 'https://live.trading212.com/api/v0/equity/'

        if not self.key_id or not self.secret:
            raise ValueError("API Keys are missing. You need to set them in the terminal.")

        auth_bytes = f"{self.key_id}:{self.secret}".encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {base64_auth}',
            'Content-Type': 'application/json'
        }

    def get_account_summary(self):
        url = f"{self.base_url}account/cash"
        response = requests.get(url, headers=self.headers)
        return response.json()
