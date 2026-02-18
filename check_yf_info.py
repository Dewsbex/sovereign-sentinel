
import yfinance as yf
import json

def check_full_info():
    t = yf.Ticker("NVDA")
    try:
        info = t.info
        print("Keys found:", list(info.keys()))
        print(f"Bid: {info.get('bid')}")
        print(f"Ask: {info.get('ask')}")
        print(f"Avg Vol: {info.get('averageVolume')}")
    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    check_full_info()
