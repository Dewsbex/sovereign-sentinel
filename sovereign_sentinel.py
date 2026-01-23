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

# Load configuration
load_dotenv()
API_KEY = os.getenv("T212_API_KEY")
API_URL = os.getenv("T212_API_URL")
RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", 0.038))
TAX_DRAG_US = float(os.getenv("TAX_DRAG_US", 0.85))
FAT_PITCH_BUFFER = float(os.getenv("FAT_PITCH_BUFFER", 0.05))

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

def get_t212_portfolio():
    headers = {"Authorization": API_KEY}
    try:
        response = requests.get(f"{API_URL}equity/portfolio", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"T212 API Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching T212 portfolio: {e}")
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
        ticker = item['ticker']
        m_data = get_market_data(ticker)
        oracle = apply_oracle_logic(
            ticker, 
            item['currentPrice'], 
            item['quantity'], 
            item['averagePrice'], 
            m_data
        )
        processed_portfolio.append({**item, **oracle})

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
    while True:
        update_system()
        # Sleep for 15 minutes as per PRD
        await asyncio.sleep(15 * 60)

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
