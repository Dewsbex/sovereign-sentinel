import os
import requests
import base64

API_KEY = "31785628ZlDtnRQJvmQjXoYmvKgAgtrWbIAXo"
API_SECRET = "pAkqASt0lyG--XY392sHodBtvi58rNmJbAYQ0jHO2DU"
URL = "https://live.trading212.com/api/v0/equity/portfolio"

print(f"Testing the two strings together...")

# 1. New string alone
r1 = requests.get(URL, headers={"Authorization": API_KEY})
print(f"New string alone: {r1.status_code}")

# 2. Previous string alone
r2 = requests.get(URL, headers={"Authorization": API_SECRET})
print(f"Previous string alone: {r2.status_code}")

# 3. Combined Basic Auth (Key:Secret)
combined = f"{API_KEY}:{API_SECRET}"
encoded = base64.b64encode(combined.encode()).decode()
r3 = requests.get(URL, headers={"Authorization": f"Basic {encoded}"})
print(f"Basic Auth (Key:Secret): {r3.status_code}")

# 4. Combined Basic Auth (Secret:Key)
combined2 = f"{API_SECRET}:{API_KEY}"
encoded2 = base64.b64encode(combined2.encode()).decode()
r4 = requests.get(URL, headers={"Authorization": f"Basic {encoded2}"})
print(f"Basic Auth (Secret:Key): {r4.status_code}")
