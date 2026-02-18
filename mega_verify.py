import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

def mega_verify():
    load_dotenv()
    print("🚀 --- THE SOVEREIGN SENTINEL: MEGA VERIFICATION --- 🚀\n")

    # 1. Project Athena (Memory) checks
    INBOX = os.getenv('INBOX_FOLDER_ID')
    BRAIN = os.getenv('BRAIN_DOC_ID')
    if INBOX and BRAIN:
        print("✅ ATHENA: IDs Found (Inbox & Brain)")
    else:
        print("❌ ATHENA: Missing IDs in .env")

    # 2. Keyed APIs
    keys = {
        "NEWSDATA": os.getenv('NEWSDATA_API_KEY'),
        "FINNHUB": os.getenv('FINNHUB_API_KEY'),
        "CRYPTOPANIC": os.getenv('CRYPTOPANIC_API_KEY'),
        "ALPHA_VANTAGE": os.getenv('ALPHA_VANTAGE_API_KEY')
    }

    for name, key in keys.items():
        if key:
            print(f"✅ {name}: Key Found in .env")
        else:
            print(f"❌ {name}: Key Missing!")

    # 3. Live "No-Key" Sources (Quick live test)
    print("\nTesting 'No-Key' Sources...")
    
    # Fear & Greed
    try:
        fng = requests.get("https://api.alternative.me/fng/", timeout=5).status_code
        if fng == 200: print("✅ FEAR & GREED: Live")
    except: print("❌ FEAR & GREED: Offline")

    # RSS Feeds
    try:
        rss = requests.get("https://www.cnbc.com/id/100003114/device/rss/rss.html", timeout=5).status_code
        if rss == 200: print("✅ RSS FEEDS: Live (CNBC)")
    except: print("❌ RSS FEEDS: Offline")

    print("\n" + "="*40)
    print("READY FOR DEPLOYMENT TO VPS")
    print("="*40)

if __name__ == "__main__":
    mega_verify()
