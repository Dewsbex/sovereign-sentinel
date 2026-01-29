import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ==============================================================================
# 1. THE CONTROL ROOM (Configuration & Context)
# ==============================================================================

# Account Logic Toggle: [ ISA Mode ] OR [ Trading/GIA Mode ]
ENVIRONMENT = os.getenv("SOVEREIGN_ENV", "ISA") # Options: "ISA", "GIA"

# Macro Variables
RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", 0.038)) # 3.8% Default
T212_MULTI_CURRENCY = os.getenv("T212_MULTI_CURRENCY", "True").lower() == "true"
DRIP_STATUS = os.getenv("DRIP_STATUS", "Active") # Impacts calculations
INTEREST_ON_CASH = os.getenv("INTEREST_ON_CASH", "True").lower() == "true" # v29.0 Cash Sweeper

# Tax Variables (UK Context)
STAMP_DUTY = 0.005 # 0.5%
US_WHT = 0.15 # 15% with W-8BEN
CGT_ALLOWANCE = 3000.0 # £3,000 (GIA Only)
DIV_ALLOWANCE = 500.0 # £500 (GIA Only)

# Sovereign Architect v27.0 Settings
CASH_HURDLE = 0.038  # 3.80% risk-free rate
TARGET_WEIGHT_CONVICTION = 0.08  # 8% for Tier 1+/1
TARGET_WEIGHT_STANDARD = 0.05    # 5% for Tier 2
MIN_TRADE_SIZE_GBP = 500.0       # Minimum trade value
UK_FRICTION = 0.005              # 0.5% Stamp Duty
US_FRICTION = 0.0015             # 0.15% FX Fee
YIELD_TRAP_THRESHOLD = 0.08      # 8% yield = potential trap
PAYOUT_TRAP_THRESHOLD = 1.00     # 100% payout ratio
PENNY_STOCK_THRESHOLD = 0.10     # £0.10 = dead asset

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
