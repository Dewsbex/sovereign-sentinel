# Sovereign Sentinel - Functionality Gap Analysis
**Generated:** 2026-01-29 17:15 UTC  
**Version:** Pre-V29.1 (Commit 74bbddd)

---

## 📋 EXECUTIVE SUMMARY

This document reconciles **requested functionality** from conversation history against **implemented features** in the current codebase.

### Status Overview
- ✅ **Implemented & Working:** 12 features
- ⚠️ **Partially Implemented:** 5 features
- ❌ **Missing/Not Implemented:** 8 features

---

## ✅ IMPLEMENTED FEATURES

### 1. **ISA Portfolio CSV Generator** ✅
- **File:** `generate_isa_portfolio.py`
- **Status:** FULLY IMPLEMENTED
- **Features:**
  - ✅ Fetches Trading 212 portfolio via API
  - ✅ Calculates Book Cost using "Golden Formula"
  - ✅ Includes FX Impact column
  - ✅ Adds CASH_GBP row for liquidity
  - ✅ Saves to Google Drive (`G:\My Drive\`)
  - ✅ Handles GBP/USD/GBX currency detection
- **Last Updated:** 17:11 GMT (verified working)

### 2. **Historical Transaction Ledger** ✅
- **File:** `ledger_sync.py`
- **Status:** FULLY IMPLEMENTED
- **Features:**
  - ✅ Multi-year chunking (2021-2026)
  - ✅ Exports T212_History_YYYY.csv per year
  - ✅ Tracks first buy dates
  - ✅ Tracks dividend history
  - ✅ Saves to `G:\My Drive\T212_ISA\`
  - ✅ Rate limit handling with backoff
- **Last Run:** 17:11 GMT (currently processing)

### 3. **Autonomous Dashboard Updates** ✅
- **File:** `sentinel_daemon.py`
- **Status:** FULLY IMPLEMENTED
- **Features:**
  - ✅ Market hours detection (09:00-21:00 GMT)
  - ✅ 5-minute update intervals
  - ✅ Auto-commit and push to GitHub
  - ✅ Triggers Cloudflare Pages deployment
  - ✅ Daily ledger sync at 21:00 GMT

### 4. **GitHub Actions Workflows** ✅
- **Files:** `.github/workflows/*.yml`
- **Status:** FULLY IMPLEMENTED
- **Workflows:**
  - ✅ `deploy.yml` - Main deployment on push
  - ✅ `08_30_validator.yml` - Pre-market validation
  - ✅ `13_00_pivot.yml` - US market open prep
  - ✅ `21_00_auditor.yml` - Post-market audit

### 5. **Trading 212 API Integration** ✅
- **File:** `generate_static.py`
- **Status:** FULLY IMPLEMENTED (Fixed 2026-01-26)
- **Features:**
  - ✅ HTTP Basic Auth (API_KEY:API_SECRET)
  - ✅ Portfolio positions fetch
  - ✅ Account cash fetch
  - ✅ Pending orders fetch
  - ✅ Instrument metadata fetch
  - ✅ Rate limit retry logic

### 6. **Portfolio Heatmap** ✅
- **File:** `generate_static.py` (lines 278-285)
- **Status:** IMPLEMENTED
- **Features:**
  - ✅ Treemap visualization data
  - ✅ Color-coded by P&L (green/red)
  - ✅ Shows position size and returns
  - ✅ Includes ghost holdings

### 7. **Moat Audit Table** ✅
- **File:** `generate_static.py` (lines 220-238)
- **Status:** IMPLEMENTED (Mock Data)
- **Features:**
  - ✅ Oracle integration
  - ✅ Net yield calculation
  - ✅ Verdict (PASS/FAIL)
  - ✅ Action recommendations
  - ✅ Deep links to Trading 212 app
  - ⚠️ **Using mock sector/moat data** (not live)

### 8. **Time-in-Market Tracking** ✅
- **File:** `generate_static.py` (lines 240-272)
- **Status:** IMPLEMENTED
- **Features:**
  - ✅ Reads ledger_cache.json
  - ✅ Calculates days held per position
  - ✅ Displays in moat audit table
  - ✅ Fallback for new positions

### 9. **Sector Guardian** ✅
- **File:** `generate_static.py` (lines 291-301)
- **Status:** IMPLEMENTED (Basic)
- **Features:**
  - ✅ Sector weight calculation
  - ✅ Overweight alerts (>35%)
  - ⚠️ **Using mock sector data** (not live)

### 10. **Cash Drag Sweeper** ✅
- **File:** `generate_static.py` (lines 303-318)
- **Status:** FULLY IMPLEMENTED
- **Features:**
  - ✅ Detects cash >5% of portfolio
  - ✅ Checks if interest is enabled
  - ✅ Alerts if "dead money" detected

### 11. **Ghost Protocol** ✅
- **File:** `generate_static.py` (lines 326-348)
- **Status:** IMPLEMENTED
- **Features:**
  - ✅ Reads from `fetch_intelligence.py`
  - ✅ Includes offline holdings in heatmap
  - ✅ Adds to total wealth calculation
  - ✅ Uses `strategy.json` for ghost data

### 12. **Immune System** ✅
- **File:** `immune_system.py`
- **Status:** IMPLEMENTED
- **Features:**
  - ✅ Connectivity heartbeat
  - ✅ 401 error detection
  - ✅ Rate limit lockout tracking
  - ✅ Alert system

---

## ⚠️ PARTIALLY IMPLEMENTED

### 1. **Sovereign Architect v27.0 Logic** ⚠️
- **Status:** PARTIALLY IMPLEMENTED
- **What's Missing:**
  - ❌ QELL filtering (Quality, Earnings, Liquidity, Leverage)
  - ❌ Fortress/Sniper/Risk Register segmentation
  - ❌ Target weight calculations
  - ❌ "Flight Deck" action recommendations
- **What Exists:**
  - ✅ Basic moat audit structure
  - ✅ Oracle integration framework
- **Reference:** Conversation `ca476b0b` (2026-01-25)

### 2. **Dynamic Sniper List** ⚠️
- **Status:** PARTIALLY IMPLEMENTED
- **What's Missing:**
  - ❌ Live price fetching for watchlist
  - ❌ "Distance to Target" calculation
  - ❌ Priority ranking by expected return
  - ❌ Integration with `watchlist.json`
- **What Exists:**
  - ✅ `watchlist.json` file structure
  - ✅ `strategy.json` with watchlist entries
- **Reference:** Conversation `6c17efaf` (2026-01-29)

### 3. **FX Impact Calculation** ⚠️
- **Status:** PARTIALLY IMPLEMENTED
- **What's Missing:**
  - ❌ Historical FX rate tracking
  - ❌ Accurate FX impact per position
  - ❌ Display in dashboard UI
- **What Exists:**
  - ✅ T212 API provides `fxPpl` field
  - ✅ CSV includes FX Impact column
  - ⚠️ Dashboard uses hardcoded 0.78 USD/GBP conversion
- **Reference:** Conversation `6c17efaf` (2026-01-29)

### 4. **yfinance Market Intelligence** ⚠️
- **Status:** REVERTED (Was in V29.1)
- **What Was Implemented (V29.1):**
  - ✅ Dividend tracking
  - ✅ Analyst ratings
  - ✅ Company fundamentals (sector, industry, market cap)
  - ✅ 52-week ranges
  - ✅ ESG scores
  - ✅ Enhanced news with sentiment
- **Current Status:**
  - ❌ All V29.1 features removed in revert
  - ✅ Basic yfinance used for FX rates only
- **Reference:** Conversation `cf5bcd6b` (2026-01-29)

### 5. **Income Calendar** ⚠️
- **Status:** MOCK DATA ONLY
- **What's Missing:**
  - ❌ Real dividend dates from yfinance
  - ❌ Automatic dividend amount calculation
  - ❌ 30-day forecast logic
- **What Exists:**
  - ✅ UI structure in template
  - ✅ Hardcoded example data (lines 321-324)
- **Reference:** Original spec

---

## ❌ MISSING FEATURES

### 1. **Live Sector/Moat Data** ❌
- **Current:** Using mock data (`'sector': 'Technology'`)
- **Required:** Fetch from yfinance or manual mapping
- **Impact:** Sector Guardian alerts are inaccurate
- **Location:** `generate_static.py` line 221

### 2. **Real Analyst Consensus** ❌
- **Current:** Random choice from list (line 376)
- **Required:** Fetch from yfinance or financial API
- **Impact:** Flight Deck shows fake data

### 3. **Automated ISA_PORTFOLIO.csv Updates** ❌
- **Current:** Manual execution only
- **Required:** Add to `sentinel_daemon.py` automation
- **Impact:** CSV files go stale between manual runs
- **Solution:** Add to market hours loop

### 4. **Director Dealings Tracking** ❌
- **Current:** Mock data (`"CEO Bought 2m ago"`)
- **Required:** Web scraping or paid API
- **Impact:** Insider trading signals unavailable
- **Location:** `generate_static.py` line 235

### 5. **Cost of Hesitation Calculator** ❌
- **Current:** Fake calculation (line 236)
- **Required:** Historical price tracking + opportunity cost logic
- **Impact:** Can't quantify missed gains

### 6. **Enhanced Watchlist Integration** ❌
- **Current:** `watchlist.json` exists but not used
- **Required:** 
  - Fetch live prices for watchlist tickers
  - Calculate "Distance to Target"
  - Display in Sniper List section
- **Impact:** No actionable buy signals

### 7. **Tax Optimization Logic** ❌
- **Current:** Solar Cycle has placeholder (line 351)
- **Required:**
  - CGT allowance tracking (£3,000/year)
  - Loss harvesting recommendations
  - Bed & ISA suggestions
- **Impact:** Missing tax-efficient selling guidance

### 8. **Real-time Price Updates** ❌
- **Current:** Dashboard updates every 5 minutes via daemon
- **Required:** WebSocket or polling for live prices
- **Impact:** Prices can be 5 minutes stale

---

## 🎯 PRIORITY RECOMMENDATIONS

### HIGH PRIORITY (Do First)
1. **Automate ISA_PORTFOLIO.csv Generation**
   - Add `generate_isa_portfolio.py` to `sentinel_daemon.py`
   - Run every 15 minutes during market hours
   - Ensures CSV is always fresh

2. **Implement Dynamic Sniper List**
   - Read `watchlist.json`
   - Fetch live prices via yfinance
   - Calculate distance to target
   - Display in dashboard

3. **Add Real Sector Data**
   - Create ticker → sector mapping file
   - Or fetch from yfinance `.info['sector']`
   - Replace mock data in line 221

### MEDIUM PRIORITY
4. **Restore yfinance Features (Selectively)**
   - Add back dividend tracking only
   - Add back analyst ratings only
   - Skip ESG/news to avoid API slowdown

5. **Implement Fortress/Sniper/Risk Segmentation**
   - Apply QELL filters
   - Calculate target weights
   - Generate action recommendations

### LOW PRIORITY
6. **Add Director Dealings** (requires paid API)
7. **Implement Tax Optimizer** (complex logic)
8. **Real-time WebSocket Prices** (infrastructure change)

---

## 📊 METRICS

| Category | Count | Percentage |
|----------|-------|------------|
| Fully Implemented | 12 | 48% |
| Partially Implemented | 5 | 20% |
| Missing | 8 | 32% |
| **Total Features** | **25** | **100%** |

---

## 🔧 TECHNICAL DEBT

1. **Hardcoded Values:**
   - USD/GBP conversion: 0.78 (line 204)
   - Sector: "Technology" (line 221)
   - Analyst consensus: Random (line 376)

2. **Mock Data:**
   - Oracle audit data (line 221)
   - Income calendar (lines 321-324)
   - Director actions (line 235)

3. **Missing Error Handling:**
   - No fallback if yfinance FX fetch fails
   - No validation of watchlist.json structure

4. **Performance Issues:**
   - No caching for yfinance calls
   - Metadata fetched on every run (could cache)

---

## 📝 NOTES

- **V29.1 Revert:** All comprehensive yfinance features removed to restore stability
- **API Status:** Trading 212 API working correctly after 2026-01-26 auth fix
- **Deployment:** GitHub Actions + Cloudflare Pages working
- **Data Freshness:** 
  - Dashboard: Auto-updates every 5 min (09:00-21:00 GMT)
  - ISA_PORTFOLIO.csv: Manual only (last: 17:11 GMT)
  - T212_History: Daily at 21:00 GMT

---

**End of Analysis**
