"""
Wealth Seeker v1.9.1 - Data Universe Generator
==============================================

Generates data/instruments.json with 100+ Tier 1 stocks across:
- US Clusters: Trinity (NVDA/TSLA/MSTR), Semiconductors, Software, Crypto, Biotech, Clean Energy, China ADRs, Consumer
- UK Sovereign Cluster: LSE blue chips (.L tickers)

This file MUST run on system startup to populate the Manual Hub search.
"""

import json
import os
from datetime import datetime

# MASTER UNIVERSE: The 100+ Tier 1 Stocks
# Defined by Cluster and Intraday Profile for the Sovereign Sentinel
MASTER_UNIVERSE = [
    # --- THE TRINITY (Benchmarks) ---
    {"ticker": "NVDA", "company": "NVIDIA Corporation", "cluster": "Trinity", "sector": "Semiconductors", "profile": "Gamma Sovereign; 3-4% daily range", "isa": True},
    {"ticker": "TSLA", "company": "Tesla Inc", "cluster": "Trinity", "sector": "Autos/AI", "profile": "Retail Sentiment; Beta > 2.0", "isa": True},
    {"ticker": "MSTR", "company": "MicroStrategy", "cluster": "Trinity", "sector": "Software/Crypto", "profile": "Leveraged Bitcoin proxy; opening gaps", "isa": True},

    # --- CLUSTER A: SEMICONDUCTOR SUPPLY CHAIN ---
    {"ticker": "AMD", "company": "Advanced Micro Devices", "cluster": "Cluster A", "sector": "Semiconductors", "profile": "High Beta; Sympathy play to NVDA", "isa": True},
    {"ticker": "AVGO", "company": "Broadcom", "cluster": "Cluster A", "sector": "Networking/AI", "profile": "High unit price; reliable trend", "isa": True},
    {"ticker": "MU", "company": "Micron Technology", "cluster": "Cluster A", "sector": "Memory", "profile": "Cyclical; sensitive to memory prices", "isa": True},
    {"ticker": "TSM", "company": "Taiwan Semiconductor", "cluster": "Cluster A", "sector": "Foundry", "profile": "Geopolitical risk; prone to gaps", "isa": True},
    {"ticker": "QCOM", "company": "Qualcomm", "cluster": "Cluster A", "sector": "Mobile", "profile": "Liquid; moderate volatility", "isa": True},
    {"ticker": "INTC", "company": "Intel Corporation", "cluster": "Cluster A", "sector": "IDM", "profile": "Turnaround play; high volume", "isa": True},
    {"ticker": "AMAT", "company": "Applied Materials", "cluster": "Cluster A", "sector": "Equipment", "profile": "Trend following; deep liquidity", "isa": True},
    {"ticker": "LRCX", "company": "Lam Research", "cluster": "Cluster A", "sector": "Equipment", "profile": "Wide range; clean trends", "isa": True},
    {"ticker": "KLAC", "company": "KLA Corp", "cluster": "Cluster A", "sector": "Metrology", "profile": "Low liquidity/high spread warning", "isa": True},
    {"ticker": "MRVL", "company": "Marvell Technology", "cluster": "Cluster A", "sector": "Data Center", "profile": "High Beta to AI theme", "isa": True},
    {"ticker": "ADI", "company": "Analog Devices", "cluster": "Cluster A", "sector": "Analog", "profile": "Lower volatility; defensive", "isa": True},
    {"ticker": "TXN", "company": "Texas Instruments", "cluster": "Cluster A", "sector": "Analog", "profile": "Low Beta; mean reversion", "isa": True},
    {"ticker": "ON", "company": "ON Semiconductor", "cluster": "Cluster A", "sector": "Power/Auto", "profile": "High EV correlation", "isa": True},
    {"ticker": "MCHP", "company": "Microchip Technology", "cluster": "Cluster A", "sector": "Microcontrollers", "profile": "Cyclical/Industrial", "isa": True},
    {"ticker": "NXPI", "company": "NXP Semiconductors", "cluster": "Cluster A", "sector": "Auto", "profile": "EV supply chain proxy", "isa": True},
    {"ticker": "TER", "company": "Teradyne", "cluster": "Cluster A", "sector": "Testing/Robotics", "profile": "Automation theme", "isa": True},
    {"ticker": "SWKS", "company": "Skyworks Solutions", "cluster": "Cluster A", "sector": "RF/Mobile", "profile": "Apple supplier correlation", "isa": True},
    {"ticker": "MPWR", "company": "Monolithic Power", "cluster": "Cluster A", "sector": "Power Mgmt", "profile": "High volatility; low float", "isa": True},
    {"ticker": "STM", "company": "STMicroelectronics", "cluster": "Cluster A", "sector": "Ind/Auto", "profile": "Euro-Zone correlation", "isa": True},
    {"ticker": "GFS", "company": "GlobalFoundries", "cluster": "Cluster A", "sector": "Foundry", "profile": "Value/Cyclical", "isa": True},
    {"ticker": "ARM", "company": "Arm Holdings", "cluster": "Cluster A", "sector": "Chip Design", "profile": "Massive volatility; float-driven", "isa": True},
    {"ticker": "SMCI", "company": "Super Micro Computer", "cluster": "Cluster A", "sector": "Server/AI", "profile": "Extreme volatility; Monitor listing status", "isa": False},

    # --- CLUSTER B: HIGH-VELOCITY SOFTWARE ---
    {"ticker": "PLTR", "company": "Palantir Technologies", "cluster": "Cluster B", "sector": "Big Data/AI", "profile": "Extreme liquidity; Retail favorite", "isa": True},
    {"ticker": "APP", "company": "AppLovin", "cluster": "Cluster B", "sector": "AdTech/AI", "profile": "Top momentum; RVOL > 2.0", "isa": True},
    {"ticker": "CRM", "company": "Salesforce", "cluster": "Cluster B", "sector": "SaaS", "profile": "Large cap anchor", "isa": True},
    {"ticker": "ADBE", "company": "Adobe", "cluster": "Cluster B", "sector": "Creative SaaS", "profile": "High price; AI theme", "isa": True},
    {"ticker": "ORCL", "company": "Oracle", "cluster": "Cluster B", "sector": "Cloud", "profile": "Breakout/Trend", "isa": True},
    {"ticker": "INTU", "company": "Intuit", "cluster": "Cluster B", "sector": "FinTech SaaS", "profile": "Defensive growth", "isa": True},
    {"ticker": "NOW", "company": "ServiceNow", "cluster": "Cluster B", "sector": "Workflow", "profile": "Institutional accumulation", "isa": True},
    {"ticker": "PANW", "company": "Palo Alto Networks", "cluster": "Cluster B", "sector": "Cyber", "profile": "Sector leader; news-sensitive", "isa": True},
    {"ticker": "CRWD", "company": "CrowdStrike", "cluster": "Cluster B", "sector": "Cyber", "profile": "Crisis volatility", "isa": True},
    {"ticker": "FTNT", "company": "Fortinet", "cluster": "Cluster B", "sector": "Cyber", "profile": "Value/Growth hybrid", "isa": True},
    {"ticker": "SNPS", "company": "Synopsys", "cluster": "Cluster B", "sector": "EDA", "profile": "Chip design; low volatility", "isa": True},
    {"ticker": "CDNS", "company": "Cadence Design", "cluster": "Cluster B", "sector": "EDA", "profile": "Chip design", "isa": True},
    {"ticker": "ZS", "company": "Zscaler", "cluster": "Cluster B", "sector": "Cyber", "profile": "High Beta growth", "isa": True},
    {"ticker": "NET", "company": "Cloudflare", "cluster": "Cluster B", "sector": "Edge Cloud", "profile": "Retail favorite; volatile", "isa": True},
    {"ticker": "DDOG", "company": "Datadog", "cluster": "Cluster B", "sector": "Observability", "profile": "Cloud usage proxy", "isa": True},
    {"ticker": "MDB", "company": "MongoDB", "cluster": "Cluster B", "sector": "Database", "profile": "Extreme ATR; wide spreads", "isa": True},
    {"ticker": "TEAM", "company": "Atlassian", "cluster": "Cluster B", "sector": "Collaboration", "profile": "Growth/Volatile", "isa": True},
    {"ticker": "ADSK", "company": "Autodesk", "cluster": "Cluster B", "sector": "Design", "profile": "Industrial/Housing proxy", "isa": True},
    {"ticker": "U", "company": "Unity Software", "cluster": "Cluster B", "sector": "Gaming Engine", "profile": "Speculative; high Beta", "isa": True},
    {"ticker": "RBLX", "company": "Roblox", "cluster": "Cluster B", "sector": "Metaverse", "profile": "Youth demographic; high volatility", "isa": True},
    {"ticker": "TTWO", "company": "Take-Two Interactive", "cluster": "Cluster B", "sector": "Gaming", "profile": "Event-driven (GTA VI)", "isa": True},
    {"ticker": "EA", "company": "Electronic Arts", "cluster": "Cluster B", "sector": "Gaming", "profile": "Steady; lower Beta", "isa": True},
    {"ticker": "HUBS", "company": "HubSpot", "cluster": "Cluster B", "sector": "Marketing", "profile": "Mid-cap growth", "isa": True},
    {"ticker": "TYL", "company": "Tyler Technologies", "cluster": "Cluster B", "sector": "GovTech", "profile": "Defensive; low volatility", "isa": True},
    {"ticker": "PTC", "company": "PTC Inc", "cluster": "Cluster B", "sector": "IoT/Industrial", "profile": "Industrial software", "isa": True},
    {"ticker": "SNOW", "company": "Snowflake", "cluster": "Cluster B", "sector": "Cloud Infra", "profile": "Frequent 5-10% earnings gaps", "isa": True},

    # --- CLUSTER C: CRYPTO & FINTECH ---
    {"ticker": "COIN", "company": "Coinbase Global", "cluster": "Cluster C", "sector": "Exchange", "profile": "Max volatility; crypto proxy", "isa": True},
    {"ticker": "MARA", "company": "MARA Holdings", "cluster": "Cluster C", "sector": "BTC Mining", "profile": "Extreme Beta", "isa": True},
    {"ticker": "RIOT", "company": "Riot Platforms", "cluster": "Cluster C", "sector": "BTC Mining", "profile": "High correlation to MARA", "isa": True},
    {"ticker": "CLSK", "company": "CleanSpark", "cluster": "Cluster C", "sector": "BTC Mining", "profile": "Green mining; high Beta", "isa": True},
    {"ticker": "HOOD", "company": "Robinhood Markets", "cluster": "Cluster C", "sector": "Brokerage", "profile": "Retail/Crypto flow", "isa": True},
    {"ticker": "SQ", "company": "Block", "cluster": "Cluster C", "sector": "Payments", "profile": "High growth; BTC correlation", "isa": True},
    {"ticker": "PYPL", "company": "PayPal", "cluster": "Cluster C", "sector": "Payments", "profile": "Turnaround; lower Beta", "isa": True},
    {"ticker": "SOFI", "company": "SoFi Technologies", "cluster": "Cluster C", "sector": "Neobank", "profile": "Retail heavy; high volume", "isa": True},
    {"ticker": "AFRM", "company": "Affirm", "cluster": "Cluster C", "sector": "BNPL", "profile": "Interest rate sensitivity", "isa": True},
    {"ticker": "V", "company": "Visa", "cluster": "Cluster C", "sector": "Network", "profile": "Low volatility; defensive", "isa": True},
    {"ticker": "MA", "company": "Mastercard", "cluster": "Cluster C", "sector": "Network", "profile": "Low volatility; defensive", "isa": True},
    {"ticker": "FIS", "company": "Fidelity National", "cluster": "Cluster C", "sector": "Processor", "profile": "Value", "isa": True},
    {"ticker": "FISV", "company": "Fiserv", "cluster": "Cluster C", "sector": "Processor", "profile": "Value", "isa": True},
    {"ticker": "GPN", "company": "Global Payments", "cluster": "Cluster C", "sector": "Processor", "profile": "Value", "isa": True},
    {"ticker": "TOST", "company": "Toast", "cluster": "Cluster C", "sector": "Restaurant Tech", "profile": "High Beta growth", "isa": True},

    # --- CLUSTER D: BIOTECH & PHARMA ---
    {"ticker": "MRNA", "company": "Moderna", "cluster": "Cluster D", "sector": "mRNA", "profile": "High volatility; news driven", "isa": True},
    {"ticker": "CRSP", "company": "CRISPR Therapeutics", "cluster": "Cluster D", "sector": "Gene Editing", "profile": "Speculative; massive volatility", "isa": True},
    {"ticker": "VRTX", "company": "Vertex Pharmaceuticals", "cluster": "Cluster D", "sector": "CF/Pain", "profile": "Structural growth", "isa": True},
    {"ticker": "REGN", "company": "Regeneron", "cluster": "Cluster D", "sector": "Oncology", "profile": "High unit price", "isa": True},
    {"ticker": "GILD", "company": "Gilead Sciences", "cluster": "Cluster D", "sector": "Virology", "profile": "Value/Yield", "isa": True},
    {"ticker": "AMGN", "company": "Amgen", "cluster": "Cluster D", "sector": "Pharma", "profile": "Dow defensive", "isa": True},
    {"ticker": "BIIB", "company": "Biogen", "cluster": "Cluster D", "sector": "Neuro", "profile": "Binary event risk", "isa": True},
    {"ticker": "ILMN", "company": "Illumina", "cluster": "Cluster D", "sector": "Genomics", "profile": "Turnaround volatility", "isa": True},
    {"ticker": "LLY", "company": "Eli Lilly", "cluster": "Cluster D", "sector": "Pharma", "profile": "GLP-1 momentum", "isa": True},
    {"ticker": "ALNY", "company": "Alnylam", "cluster": "Cluster D", "sector": "RNAi", "profile": "High Beta", "isa": True},
    {"ticker": "INSM", "company": "Insmed", "cluster": "Cluster D", "sector": "Rare Disease", "profile": "Mid-cap volatility", "isa": True},
    {"ticker": "NTRA", "company": "Natera", "cluster": "Cluster D", "sector": "Diagnostics", "profile": "Growth/Volatile", "isa": True},

    # --- CLUSTER E: CLEAN ENERGY & EVS ---
    {"ticker": "ENPH", "company": "Enphase Energy", "cluster": "Cluster E", "sector": "Solar", "profile": "Extreme ATR; squeeze potential", "isa": True},
    {"ticker": "SEDG", "company": "SolarEdge", "cluster": "Cluster E", "sector": "Solar", "profile": "Max volatility; distressed", "isa": True},
    {"ticker": "FSLR", "company": "First Solar", "cluster": "Cluster E", "sector": "Panels", "profile": "Tariff play", "isa": True},
    {"ticker": "RUN", "company": "Sunrun", "cluster": "Cluster E", "sector": "Resi Solar", "profile": "Rate sensitive; leveraged", "isa": True},
    {"ticker": "RIVN", "company": "Rivian", "cluster": "Cluster E", "sector": "EV", "profile": "Retail speculation", "isa": True},
    {"ticker": "LCID", "company": "Lucid Group", "cluster": "Cluster E", "sector": "EV", "profile": "Short squeeze candidate", "isa": True},
    {"ticker": "ALB", "company": "Albemarle", "cluster": "Cluster E", "sector": "Lithium", "profile": "Commodity cycle", "isa": True},
    {"ticker": "PLUG", "company": "Plug Power", "cluster": "Cluster E", "sector": "Hydrogen", "profile": "Penny volatility", "isa": True},
    {"ticker": "BE", "company": "Bloom Energy", "cluster": "Cluster E", "sector": "Hydrogen", "profile": "High Beta", "isa": True},
    {"ticker": "NEM", "company": "Newmont", "cluster": "Cluster E", "sector": "Gold Mining", "profile": "High Beta to gold", "isa": True},

    # --- CLUSTER F: CHINA ADRS ---
    {"ticker": "BABA", "company": "Alibaba Group", "cluster": "Cluster F", "sector": "E-Comm", "profile": "Liquid; Amazon of China", "isa": True},
    {"ticker": "PDD", "company": "PDD Holdings", "cluster": "Cluster F", "sector": "E-Comm", "profile": "Extreme volatility", "isa": True},
    {"ticker": "JD", "company": "JD.com", "cluster": "Cluster F", "sector": "E-Comm", "profile": "Consumer proxy", "isa": True},
    {"ticker": "BIDU", "company": "Baidu", "cluster": "Cluster F", "sector": "AI/Search", "profile": "AI theme sympathy", "isa": True},
    {"ticker": "NIO", "company": "NIO Inc", "cluster": "Cluster F", "sector": "EV", "profile": "Tesla of China; retail favorite", "isa": True},
    {"ticker": "XPEV", "company": "XPeng", "cluster": "Cluster F", "sector": "EV", "profile": "High Beta EV", "isa": True},
    {"ticker": "LI", "company": "Li Auto", "cluster": "Cluster F", "sector": "EV", "profile": "Quality growth EV", "isa": True},
    {"ticker": "TCOM", "company": "Trip.com", "cluster": "Cluster F", "sector": "Travel", "profile": "Reopening play", "isa": True},
    {"ticker": "BILI", "company": "Bilibili", "cluster": "Cluster F", "sector": "Media", "profile": "Volatile; YouTube of China", "isa": True},
    {"ticker": "FUTU", "company": "Futu Holdings", "cluster": "Cluster F", "sector": "FinTech", "profile": "Brokerage; high volatility", "isa": True},
    {"ticker": "TCEHY", "company": "Tencent Holdings", "cluster": "Cluster F", "sector": "Tech", "profile": "OTC Listing", "isa": False},

    # --- CLUSTER G: CONSUMER & REAL ECONOMY ---
    {"ticker": "AMZN", "company": "Amazon.com", "cluster": "Cluster G", "sector": "E-Comm", "profile": "Mag 7; Cloud leader", "isa": True},
    {"ticker": "GOOGL", "company": "Alphabet", "cluster": "Cluster G", "sector": "Search", "profile": "AI lag trade", "isa": True},
    {"ticker": "META", "company": "Meta Platforms", "cluster": "Cluster G", "sector": "Social", "profile": "High price/range", "isa": True},
    {"ticker": "MSFT", "company": "Microsoft", "cluster": "Cluster G", "sector": "Cloud", "profile": "Low volatility", "isa": True},
    {"ticker": "NFLX", "company": "Netflix", "cluster": "Cluster G", "sector": "Media", "profile": "Subscriber driven", "isa": True},
    {"ticker": "DIS", "company": "Walt Disney", "cluster": "Cluster G", "sector": "Media", "profile": "Turnaround; liquid", "isa": True},
    {"ticker": "WBD", "company": "Warner Bros Discovery", "cluster": "Cluster G", "sector": "Media", "profile": "Debt/Leverage volatility", "isa": True},
    {"ticker": "ROKU", "company": "Roku", "cluster": "Cluster G", "sector": "Media", "profile": "High Beta; ad revenue", "isa": True},
    {"ticker": "CMG", "company": "Chipotle Mexican Grill", "cluster": "Cluster G", "sector": "Restaurant", "profile": "High growth", "isa": True},
    {"ticker": "SBUX", "company": "Starbucks", "cluster": "Cluster G", "sector": "Restaurant", "profile": "Management change volatility", "isa": True},
    {"ticker": "LULU", "company": "Lululemon", "cluster": "Cluster G", "sector": "Apparel", "profile": "Growth concerns", "isa": True},
    {"ticker": "NKE", "company": "Nike", "cluster": "Cluster G", "sector": "Apparel", "profile": "Turnaround play", "isa": True},
    {"ticker": "DKNG", "company": "DraftKings", "cluster": "Cluster G", "sector": "Gaming", "profile": "Sports seasonality", "isa": True},
    {"ticker": "UBER", "company": "Uber Technologies", "cluster": "Cluster G", "sector": "Transport", "profile": "Steady growth", "isa": True},
    {"ticker": "ABNB", "company": "Airbnb", "cluster": "Cluster G", "sector": "Travel", "profile": "Volatile earnings", "isa": True},
    {"ticker": "BKNG", "company": "Booking Holdings", "cluster": "Cluster G", "sector": "Travel", "profile": "Highest unit price; huge spreads", "isa": True},
    {"ticker": "COST", "company": "Costco", "cluster": "Cluster G", "sector": "Retail", "profile": "Stability; defensive", "isa": True},
    {"ticker": "WMT", "company": "Walmart", "cluster": "Cluster G", "sector": "Retail", "profile": "Defensive", "isa": True},
    {"ticker": "TGT", "company": "Target", "cluster": "Cluster G", "sector": "Retail", "profile": "Consumer health proxy", "isa": True},
    {"ticker": "HD", "company": "Home Depot", "cluster": "Cluster G", "sector": "Retail", "profile": "Housing proxy", "isa": True},
    {"ticker": "LOW", "company": "Lowe's", "cluster": "Cluster G", "sector": "Retail", "profile": "Housing proxy", "isa": True},
    {"ticker": "CAT", "company": "Caterpillar", "cluster": "Cluster G", "sector": "Industrial", "profile": "Global economy proxy", "isa": True},
    {"ticker": "DE", "company": "Deere & Co", "cluster": "Cluster G", "sector": "Ag/Ind", "profile": "Agriculture cycle", "isa": True},
    {"ticker": "BA", "company": "Boeing", "cluster": "Cluster G", "sector": "Aero", "profile": "Crisis volatility", "isa": True},
    {"ticker": "GE", "company": "GE Aerospace", "cluster": "Cluster G", "sector": "Aero", "profile": "Breakout trend", "isa": True},
    {"ticker": "JPM", "company": "JPMorgan Chase", "cluster": "Cluster G", "sector": "Bank", "profile": "Rate proxy", "isa": True},
    {"ticker": "GS", "company": "Goldman Sachs", "cluster": "Cluster G", "sector": "Bank", "profile": "Market proxy", "isa": True},
    {"ticker": "CVX", "company": "Chevron", "cluster": "Cluster G", "sector": "Energy", "profile": "Oil Beta", "isa": True},
    {"ticker": "XOM", "company": "Exxon Mobil", "cluster": "Cluster G", "sector": "Energy", "profile": "Oil Beta", "isa": True},
    {"ticker": "SLB", "company": "Schlumberger", "cluster": "Cluster G", "sector": "Energy Svc", "profile": "High Beta energy", "isa": True},

    # --- CLUSTER H: UK SOVEREIGN (LSE) ---
    {"ticker": "RR.L", "company": "Rolls-Royce Holdings", "cluster": "Cluster H", "sector": "Aero/Defense", "profile": "Turnaround; high beta", "isa": True},
    {"ticker": "AZN.L", "company": "AstraZeneca", "cluster": "Cluster H", "sector": "Pharma", "profile": "Defensive growth", "isa": True},
    {"ticker": "SHEL.L", "company": "Shell", "cluster": "Cluster H", "sector": "Energy", "profile": "Oil Beta; yield", "isa": True},
    {"ticker": "BP.L", "company": "BP", "cluster": "Cluster H", "sector": "Energy", "profile": "Oil Beta; yield", "isa": True},
    {"ticker": "HSBA.L", "company": "HSBC Holdings", "cluster": "Cluster H", "sector": "Bank", "profile": "Rate proxy", "isa": True},
    {"ticker": "LLOY.L", "company": "Lloyds Banking Group", "cluster": "Cluster H", "sector": "Bank", "profile": "Domestic cycle", "isa": True},
    {"ticker": "BARC.L", "company": "Barclays", "cluster": "Cluster H", "sector": "Bank", "profile": "Volatility", "isa": True},
    {"ticker": "NG.L", "company": "National Grid", "cluster": "Cluster H", "sector": "Utility", "profile": "Defensive; yield", "isa": True},
    {"ticker": "VOD.L", "company": "Vodafone Group", "cluster": "Cluster H", "sector": "Telecom", "profile": "Value trap/turnaround", "isa": True},
    {"ticker": "TSCO.L", "company": "Tesco", "cluster": "Cluster H", "sector": "Retail", "profile": "Defensive staple", "isa": True}
]


def generate_dual_ledger():
    """
    v1.9.4 DUAL-LEDGER SYSTEM
    =========================
    
    Generates TWO separate data files:
    
    1. master_universe.json - Job C autonomous trading ONLY (100+ vetted Tier 1)
       - Purpose: High-velocity, low-hallucination source for ORB scalper
       - Safety: Prevents 429 rate limits and ticker confusion
    
    2. instruments.json - Manual Hub + Job A research (retains full 12,000+ from T212 API)
       - Purpose: Discovery engine for moat research and manual fund purchases
       - Protection: 90% fuzzy match validation ensures data quality
    """
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # LEDGER 1: Master Universe (Job C Only)
    master_data = {
        "metadata": {
            "version": "1.9.4",
            "generated": datetime.utcnow().isoformat() + 'Z',
            "count": len(MASTER_UNIVERSE),
            "purpose": "Job C Autonomous Trading - Vetted Tier 1 Only",
            "source": "Wealth Seeker Platinum Master",
            "clusters": {
                "Trinity": "Benchmarks (NVDA, TSLA, MSTR)",
                "Cluster A": "Semiconductor Supply Chain",
                "Cluster B": "High-Velocity Software",
                "Cluster C": "Crypto & FinTech",
                "Cluster D": "Biotech & Pharma",
                "Cluster E": "Clean Energy & EVs",
                "Cluster F": "China ADRs",
                "Cluster G": "Consumer & Real Economy",
                "Cluster H": "UK Sovereign (LSE)"
            }
        },
        "instruments": MASTER_UNIVERSE
    }
    
    master_path = "data/master_universe.json"
    with open(master_path, 'w') as f:
        json.dump(master_data, f, indent=4)
    
    print(f"✅ Ledger 1 (Job C): {master_path}")
    print(f"   Vetted Tier 1: {len(MASTER_UNIVERSE)} tickers")
    print(f"   ISA-eligible: {sum(1 for i in MASTER_UNIVERSE if i['isa'])}")
    print(f"   UK Sovereign (.L): {sum(1 for i in MASTER_UNIVERSE if i['ticker'].endswith('.L'))}")
    
    # LEDGER 2: Global Instrument Map (Manual Hub + Job A)
    # NOTE: instruments.json should be maintained from Trading 212 API fetch
    # We keep the master universe as a fallback if T212 fetch fails
    instruments_path = "data/instruments.json"
    
    if not os.path.exists(instruments_path):
        # Fallback: If instruments.json doesn't exist, create it from master universe
        print(f"\n⚠️  {instruments_path} not found - creating from master universe")
        print(f"   For full 12,000+ database, fetch from Trading 212 API")
        
        with open(instruments_path, 'w') as f:
            json.dump(master_data, f, indent=4)
    else:
        # instruments.json already exists (from T212 API or previous run)
        with open(instruments_path, 'r') as f:
            existing_data = json.load(f)
        
        existing_count = existing_data.get('metadata', {}).get('count', 0)
        print(f"\n✅ Ledger 2 (Manual Hub + Job A): {instruments_path}")
        print(f"   Global instruments: {existing_count:,} tickers")
        print(f"   Source: Trading 212 API (maintained)")
    
    print(f"\n🏛️ DUAL-LEDGER SYSTEM ACTIVE")
    print(f"   Job C: Hard-locked to {len(MASTER_UNIVERSE)} vetted tickers")
    print(f"   Manual Hub/Job A: Full market access for discovery")


if __name__ == "__main__":
    generate_dual_ledger()
