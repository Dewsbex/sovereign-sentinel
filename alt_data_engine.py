import os
import time
import json
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pytrends.request import TrendReq
import finnhub

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("alt_data_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AltDataEngine")

# Configuration
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")



DATA_FILE = "data/sentiment_snapshot.json"

def fetch_fear_and_greed():
    """Fetches the Crypto Fear & Greed Index (Free API)."""
    url = "https://api.alternative.me/fng/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', [])[0]
            return {
                "value": data.get('value'),
                "sentiment": data.get('value_classification')
            }
    except Exception as e:
        logger.error(f"Error fetching Fear & Greed: {e}")
    return {}

def fetch_macro_data():
    """Fetches Federal Funds Rate using Alpha Vantage."""
    if not ALPHA_VANTAGE_API_KEY:
        return {}
    url = f"https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&interval=monthly&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', [])
            if data:
                return data[0] # Latest rate
    except Exception as e:
        logger.error(f"Error fetching Macro Data: {e}")
    return {}


def fetch_pytrends(keywords=["market crash", "recession", "bull market", "buy the dip"]):
    """Fetches Google Trends interest over time."""
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload(keywords, cat=0, timeframe='now 1-H', geo='', gprop='')
        data = pytrends.interest_over_time()
        if not data.empty:
            return data.iloc[-1].to_dict() # Return latest data point
    except Exception as e:
        logger.error(f"Error fetching PyTrends: {e}")
    return {}

def fetch_rss_news():
    """Fetches breaking financial news from major RSS feeds."""
    feeds = [
        "https://www.cnbc.com/id/100003114/device/rss/rss.html", # Top News
        "https://www.reutersagency.com/feed/?best-types=business-finance&post_type=best" # Business
    ]
    all_headlines = []
    for url in feeds:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')
                for item in items[:5]:
                    all_headlines.append(item.title.text)
        except Exception as e:
            logger.error(f"Error fetching RSS {url}: {e}")
    return all_headlines

def fetch_newsdata():

    """Fetches news from NewsData.io."""
    if not NEWSDATA_API_KEY:
        return {}
    url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&language=en"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get('results', [])
    except Exception as e:
        logger.error(f"Error fetching NewsData.io: {e}")
    return []

def fetch_finnhub(ticker='SPY'):
    """Fetches market sentiment from Finnhub."""
    if not FINNHUB_API_KEY:
        return {}
    try:
        finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
        # News Sentiment (Free tier check handled in verify)
        sentiment = finnhub_client.news_sentiment(ticker)
        return sentiment
    except Exception as e:
        logger.error(f"Error fetching Finnhub: {e}")
        # Return empty if restricted
    return {}

def fetch_cryptopanic():
    """Fetches trending crypto news and sentiment."""
    if not CRYPTOPANIC_API_KEY:
        return {}
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&public=true"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get('results', [])[:10]
    except Exception as e:
        logger.error(f"Error fetching CryptoPanic: {e}")
    return []


def scrape_reddit_hot(subreddit="wallstreetbets"):
    """Scrapes Hot page of a subreddit using BeautifulSoup and Playwright."""
    from playwright.sync_api import sync_playwright
    import logging
    
    logger = logging.getLogger("RedditScraper")
    titles = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Reddit requires User-Agent to avoid blocking sometimes, though Playwright handles it well usually
            page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
            
            url = f"https://www.reddit.com/r/{subreddit}/hot/"
            logger.info(f"Navigating to {url}...")
            page.goto(url, wait_until="domcontentloaded")
            
            # Wait for content to load - Reddit is heavy JS
            page.wait_for_selector('shreddit-post', timeout=10000) 
            
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Select post titles (Reddit's DOM changes often, using loose selector or specific attribute)
            # Modern Reddit uses <shreddit-post> tags with 'post-title' attribute
            posts = soup.find_all('shreddit-post')
            for post in posts[:10]: # Top 10
                title = post.get('post-title')
                if title:
                    titles.append(title)
            
            browser.close()
            return titles
            
    except Exception as e:
        logger.error(f"Error scraping Reddit: {e}")
        return []

def save_snapshot(data):
    """Saves the aggregated data to a JSON file."""
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(snapshot, f, indent=4)
        logger.info(f"Saved sentiment snapshot to {DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving snapshot: {e}")

def main():
    logger.info("Starting Alternative Data Engine...")
    
    while True:
        try:
            logger.info("Fetching data...")
            aggregated_data = {
                "fear_and_greed": fetch_fear_and_greed(),
                "macro_data": fetch_macro_data(),
                "rss_breaking": fetch_rss_news(),
                "pytrends": fetch_pytrends(),
                "newsdata": fetch_newsdata(),
                "finnhub": fetch_finnhub(),
                "cryptopanic": fetch_cryptopanic(),
                "reddit": scrape_reddit_hot() 
            }


            save_snapshot(aggregated_data)

            
            # Sleep for 60 minutes
            logger.info("Sleeping for 60 minutes...")
            time.sleep(3600)
            
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main()
