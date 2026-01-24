import os

# ==============================================================================
# 1. THE CONTROL ROOM (Configuration & Context)
# ==============================================================================

# Account Logic Toggle: [ ISA Mode ] OR [ Trading/GIA Mode ]
ENVIRONMENT = os.getenv("SOVEREIGN_ENV", "ISA") # Options: "ISA", "GIA"

# Macro Variables
RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", 0.038)) # 3.8% Default
T212_MULTI_CURRENCY = os.getenv("T212_MULTI_CURRENCY", "True").lower() == "true"
DRIP_STATUS = os.getenv("DRIP_STATUS", "Active") # Impacts calculations

# Tax Variables (UK Context)
STAMP_DUTY = 0.005 # 0.5%
US_WHT = 0.15 # 15% with W-8BEN
CGT_ALLOWANCE = 3000.0 # £3,000 (GIA Only)
DIV_ALLOWANCE = 500.0 # £500 (GIA Only)

# T212 API Credentials
T212_API_KEY = os.getenv("T212_API_KEY")
T212_API_SECRET = os.getenv("T212_API_SECRET")

# Ticker Mapping Table (T212 <-> Google/Yahoo)
TICKER_MAPPING = {
    "VODl_EQ": "VOD.L",
    "RR.L": "RR.L",
    "AAPL_US_EQ": "AAPL",
    "TSLA_US_EQ": "TSLA"
}

def get_mapped_ticker(t212_ticker):
    return TICKER_MAPPING.get(t212_ticker, t212_ticker.replace("l_EQ", "").replace("_EQ", "").replace(".L", ""))
