import os
import time
import json
import asyncio
import logging
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from threading import Thread
import config  # Using the standardized mapper

# Load configuration
load_dotenv()
API_KEY = os.getenv("T212_API_KEY")
API_URL = os.getenv("T212_API_URL", "https://live.trading212.com/api/v0/").strip()
if not API_URL.endswith('/'): API_URL += '/'
RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", 0.038))
TAX_DRAG_US = float(os.getenv("TAX_DRAG_US", 0.85))
FAT_PITCH_BUFFER = float(os.getenv("FAT_PITCH_BUFFER", 0.05))

# Persistent Session for connection pooling
session = requests.Session()

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Sovereign Sentinel")
templates = Jinja2Templates(directory="templates")

# Global State
SYSTEM_STATE = {
    "portfolio": [],
    "watchlist": [],
    "last_update": None,
    "alerts": []
}

def make_request_with_retry(url, headers, max_retries=3):
    """v29.2 Golden Fix: Ultra-Sequential Fetcher. 3.5s Mandatory Cooldown."""
    for attempt in range(max_retries):
        try:
            # 1. Check for Security Lockout
            if os.path.exists('401_block.lock'):
                st = os.path.getmtime('401_block.lock')
                if (time.time() - st) < 300:
                    logger.warning("[BLOCK] 401 Security Lockout active. Aborting request.")
                    return None
                else:
                    os.remove('401_block.lock')

            r = session.get(url, headers=headers, timeout=15)
            logger.info(f"      [API] {url.split('/')[-1]} -> {r.status_code}")
            
            if r.status_code == 429:
                wait_time = (attempt + 1) * 15
                logger.warning(f"      [429] Rate Limit. Cooling down {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            if r.status_code == 401:
                with open('401_block.lock', 'w') as f: f.write('BLOCK')
                logger.error("      [401] Unauthorized. Lockout triggered for 300s.")
                return r

            # v29.2: MANDATORY 3.5s delay after EVERY call
            time.sleep(3.5)
            return r
        except Exception as e:
            logger.error(f"      [ERR] {e}")
            time.sleep(5)
    return None

def get_t212_portfolio():
    headers = {
        "Authorization": API_KEY,
        "User-Agent": "Mozilla/5.0 (SovereignSentinel/1.0)",
        "Content-Type": "application/json"
    }
    response = make_request_with_retry(f"{API_URL}equity/portfolio", headers)
    if response and response.status_code == 200:
        return response.json()
    return []

def get_market_data(ticker):
    try:
        # Simple heuristic for US stocks in T212: usually no suffix or .US (yfinance uses no suffix)
        # For UK, T212 might use ticker_LSE, yfinance uses ticker.L
        yf_ticker = ticker.replace("_LSE", ".L")
        stock = yf.Ticker(yf_ticker)
        info = stock.info
        
        return {
            "trailingPE": info.get("trailingPE"),
            "dividendYield": info.get("dividendYield", 0) or 0,
            "roic": info.get("returnOnCapital", 0) or 0,
            "summary": info.get("longBusinessSummary", ""),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "country": info.get("country", "")
        }
    except Exception as e:
        logger.error(f"Error fetching market data for {ticker}: {e}")
        return None

def apply_oracle_logic(ticker, current_price, quantity, avg_price, market_data):
    if not market_data:
        return {"status": "UNKNOWN", "net_yield": 0, "verdict": "No Data"}

    raw_yield = market_data["dividendYield"]
    is_us = market_data["country"] == "United States"
    net_yield = raw_yield * TAX_DRAG_US if is_us else raw_yield
    
    # Logic Block 1: Cash Hurdle
    # Conservative Growth Rate - for simplicity using a default or fetching from historical if needed
    # Here we use a placeholder or assumed 2% if not in watchlist
    growth_rate = 0.02 
    
    status = "PASS"
    verdict = "Fair Value"
    action = "HOLD"
    color = "green"

    if (net_yield + growth_rate) < RISK_FREE_RATE:
        status = "FAIL"
        verdict = "Yield Erosion"
        action = "TRIM"
        color = "red"
        alert_msg = f"⚠️ {ticker} Yield Erosion. Net Yield now {net_yield:.1%}. Below Cash Hurdle ({RISK_FREE_RATE:.1%}). Investigate."
        SYSTEM_STATE["alerts"].append({"type": "VIOLATION", "message": alert_msg, "time": datetime.now().isoformat()})
        print(alert_msg)

    return {
        "ticker": ticker,
        "price": current_price,
        "net_yield": net_yield,
        "verdict": verdict,
        "action": action,
        "color": color,
        "status": status
    }

def update_system():
    logger.info("Starting System Update...")
    
    # 1. Fetch T212 Portfolio
    t212_data = get_t212_portfolio()
    processed_portfolio = []
    
    for item in t212_data:
        ticker_raw = item['ticker']
        
        # v29.2 Golden Fix: Data Reconciliation
        # 1. Normalize Ticker using the central config
        ticker = config.get_mapped_ticker(ticker_raw)
        
        # 2. Currency Normalization (The Pence vs Pounds Fix)
        currency = item.get('currency', '')
        raw_cur_price = item['currentPrice']
        raw_avg_price = item['averagePrice']
        
        # Detect UK stocks quoted in Pence (GBX)
        is_uk = (currency in ['GBX', 'GBp'] or '_GB_' in ticker_raw or ticker_raw.endswith('.L'))
        # Safety heuristic: US giants aren't usually priced at 1000+ per share in GBP accounts
        if not ('_US_' in ticker_raw) and raw_cur_price > 180.0: is_uk = True
        
        fx_factor = 0.01 if is_uk else 1.0
        current_price = raw_cur_price * fx_factor
        avg_price = raw_avg_price * fx_factor
        
        # 3. Fetch Market Intel
        m_data = get_market_data(ticker)
        time.sleep(0.5) # Anti-rate limit for yfinance
        
        oracle = apply_oracle_logic(
            ticker, 
            current_price, 
            item['quantity'], 
            avg_price, 
            m_data
        )
        processed_portfolio.append({**item, **oracle, 'ticker': ticker, 'currentPrice': current_price})

    # 2. Fetch Watchlist
    try:
        with open("watchlist.json", "r") as f:
            watchlist = json.load(f)
    except:
        watchlist = []

    processed_watchlist = []
    for item in watchlist:
        ticker = item['ticker']
        target = item['target_price']
        m_data = get_market_data(ticker)
        
        if m_data and m_data['currentPrice']:
            price = m_data['currentPrice']
            status = "WAIT"
            verdict = "Fair Value"
            action = "WAIT"
            color = "yellow"

            # Logic Block 2: Fat Pitch scanner
            if price <= target:
                status = "EXECUTE"
                verdict = "Fat Pitch Active"
                action = "BUY"
                color = "green"
                alert_msg = f"🎯 {ticker} Fat Pitch Active. Price: ${price}. Target: ${target}. EXECUTE."
                SYSTEM_STATE["alerts"].append({"type": "OPPORTUNITY", "message": alert_msg, "time": datetime.now().isoformat()})
                print(alert_msg)
            elif price <= (target * (1 + FAT_PITCH_BUFFER)):
                status = "WATCH"
                verdict = "Preparing"
                action = "WATCH"
                color = "yellow"

            processed_watchlist.append({
                "ticker": ticker,
                "price": price,
                "target": target,
                "verdict": verdict,
                "action": action,
                "color": color,
                "status": status
            })

    # Mock data for demonstration if portfolio is empty or for testing violations
    if not processed_portfolio:
        processed_portfolio.append({
            "ticker": "NUE",
            "currentPrice": 175.0,
            "quantity": 10,
            "averagePrice": 160.0,
            "net_yield": 0.011,
            "verdict": "Yield Erosion",
            "action": "TRIM",
            "color": "red",
            "status": "FAIL"
        })
        alert_msg = "⚠️ NUE Yield Erosion. Net Yield now 1.1%. Below Cash Hurdle (3.8%). Investigate."
        SYSTEM_STATE["alerts"].append({"type": "VIOLATION", "message": alert_msg, "time": datetime.now().isoformat()})

    SYSTEM_STATE["portfolio"] = processed_portfolio
    SYSTEM_STATE["watchlist"] = processed_watchlist
    SYSTEM_STATE["last_update"] = datetime.now().isoformat()
    logger.info("System Update Complete.")

async def background_worker():
    # Concurrency Lock (v29.2 Principle)
    if os.path.exists('sentinel.lock'):
         logger.warning("Overlap detected. sentinel.lock exists.")
    
    with open('sentinel.lock', 'w') as f:
        f.write(str(os.getpid()))

    try:
        while True:
            update_system()
            # Sleep for 15 minutes as per PRD
            await asyncio.sleep(15 * 60)
    finally:
        if os.path.exists('sentinel.lock'):
            os.remove('sentinel.lock')

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_worker())

@app.get("/")
async def get_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "portfolio": SYSTEM_STATE["portfolio"],
        "watchlist": SYSTEM_STATE["watchlist"],
        "last_update": SYSTEM_STATE["last_update"],
        "alerts": SYSTEM_STATE["alerts"][-10:] # Last 10 alerts
    })

@app.get("/api/state")
async def get_state():
    return JSONResponse(content=SYSTEM_STATE)

if __name__ == "__main__":
    import uvicorn
    # Create templates dir if not exists
    os.makedirs("templates", exist_ok=True)
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8000)
