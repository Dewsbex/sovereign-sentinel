import os
import requests
from dotenv import load_dotenv

def verify_alt_data():
    load_dotenv()
    news_key = os.getenv('NEWSDATA_API_KEY')
    finn_key = os.getenv('FINNHUB_API_KEY')
    cp_key = os.getenv('CRYPTOPANIC_API_KEY')

    print("--- Alternative Data Verification ---")

    # 1. Verify NewsData
    if news_key:
        print(f"Checking NewsData.io (Key: {news_key[:10]}...)...")
        url = f"https://newsdata.io/api/1/news?apikey={news_key}&q=test&language=en"
        try:
            res = requests.get(url)
            if res.status_code == 200:
                print("✅ NewsData: SUCCESS (Key is active)")
            else:
                print(f"❌ NewsData: FAILED ({res.status_code}): {res.text[:100]}")
        except Exception as e:
            print(f"❌ NewsData: ERROR: {e}")
    else:
        print("❌ NewsData: Key missing in .env")

    # 2. Verify Finnhub (Basic)
    if finn_key:
        print(f"\nChecking Finnhub (Key: {finn_key[:10]}...)...")
        url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={finn_key}"
        try:
            res = requests.get(url)
            if res.status_code == 200:
                print("✅ Finnhub (Basic): SUCCESS")
                print(f"   Sample Data: {res.json()}")
            else:
                print(f"❌ Finnhub (Basic): FAILED ({res.status_code}): {res.text[:100]}")
        except Exception as e:
            print(f"❌ Finnhub: ERROR: {e}")
    else:
        print("❌ Finnhub: Key missing in .env")

    # 3. Verify CryptoPanic
    if cp_key:
        print(f"\nChecking CryptoPanic (Key: {cp_key[:10]}...)...")
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token={cp_key}&public=true"
        try:
            res = requests.get(url)
            if res.status_code == 200:
                print("✅ CryptoPanic: SUCCESS (Key is active)")
            else:
                print(f"❌ CryptoPanic: FAILED ({res.status_code}): {res.text[:100]}")
        except Exception as e:
            print(f"❌ CryptoPanic: ERROR: {e}")
    else:
        print("❌ CryptoPanic: Key missing in .env")

if __name__ == "__main__":
    verify_alt_data()
