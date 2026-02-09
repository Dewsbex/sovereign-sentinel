#!/usr/bin/env python3
"""Test Trading 212 API connection"""

import requests
import os

# Try header-based auth (original method)
API_KEY = os.getenv('TRADING212_API_KEY', '31785628ZJPoZDazvapbPkdrBKexWLXqJIfqe')

headers = {'Authorization': API_KEY}
url = 'https://live.trading212.com/api/v0/equity/account/cash'

print(f"Testing Trading 212 API connection...")
print(f"API Key: {API_KEY[:10]}... (first 10 chars)")
print(f"URL: {url}\n")

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Total Balance: £{data.get('total', 0):.2f}")
        print(f"Free Cash: £{data.get('free', 0):.2f}")
    elif response.status_code == 401:
        print(f"\n❌ Authentication failed - Check API key")
    else:
        print(f"\n⚠️  Unexpected response")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
