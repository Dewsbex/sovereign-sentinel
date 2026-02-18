
import yfinance as yf

def check_fast_info():
    t = yf.Ticker("NVDA")
    info = t.fast_info
    print("Keys:", info.keys())
    print("Last Price:", info.get('last_price'))
    # Check for bid/ask
    # Note: 'previous_close', 'open', 'day_high', 'day_low', 'last_price', 'last_volume', 'market_cap'
    # It might NOT have bid/ask.
    
    # Try t.info (standard info) - this is slower but might have 'bid', 'ask'
    # print("Standard Info Bid:", t.info.get('bid'))
    # print("Standard Info Ask:", t.info.get('ask'))
    
if __name__ == "__main__":
    check_fast_info()
