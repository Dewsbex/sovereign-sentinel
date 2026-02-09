# Sovereign Sentinel - Complete System Specification

**Version:** v1.4.1 (PRECISION LOCK) → v1.5.0 (LIVE EXECUTION)  
**Last Updated:** 2026-02-07

---

## 1. System Overview

**Sovereign Sentinel** is a real-time portfolio tracking and tactical trading terminal that integrates Trading 212 positions, market data, and AI-driven strategic analysis into a single-screen command center.

### Core Mission
Enable precision scalping and long-term position management through:
- Real-time momentum heatmaps
- Opening Range Breakout (ORB) detection
- One-click limit order execution
- AI-powered strategic briefs

### Technology Stack
- **Backend:** Python 3.x, Flask (planned), Jinja2 templating
- **Data Sources:** Trading 212 API, yfinance, Google Gemini Pro
- **Frontend:** Vanilla JavaScript, ApexCharts, JetBrains Mono
- **Deployment:** Cloudflare Pages (static), GitHub Actions
- **State Management:** JSON file (`live_state.json`)

---

## 2. Current Architecture (v1.4.1)

### 2.1 Data Pipeline

```
┌─────────────────┐
│ Trading 212 API │ (Positions, Orders, Account)
└────────┬────────┘
         │
         ├──► generate_isa_portfolio.py ──► t212_portfolio.json
         │
┌────────▼────────┐
│  Sentinel Pot   │ (realized_pnl.json)
└────────┬────────┘
         │
         ├──► generate_static.py ──► fortress_state.json
         │
┌────────▼────────┐
│  generate_ui.py │
└────────┬────────┘
         │
         └──► index.html (Dashboard)
```

### 2.2 File Structure

```
Sovereign-Sentinel/
├── generate_ui.py              # Main dashboard generator
├── generate_isa_portfolio.py   # Trading 212 position fetcher
├── generate_static.py          # Fortress module (sentinel pot)
├── trading212_client.py        # ✅ NEW: API client (Phase 2)
├── test_trading212.py          # ✅ NEW: API test suite
├── templates/
│   └── base.html               # Dashboard UI template
├── data/
│   ├── live_state.json         # Aggregated dashboard state
│   ├── t212_portfolio.json     # Trading 212 positions
│   ├── fortress_state.json     # Sentinel pot state
│   └── realized_pnl.json       # Trade history
├── docs/
│   ├── trading212_api_schemas.md  # ✅ NEW: API reference
│   ├── trading212_setup.md        # ✅ NEW: Setup guide
│   └── SYSTEM_SPEC.md             # This file
└── .github/workflows/
    └── seeker.yml              # GitHub Actions deployment
```

---

## 3. UI Components (v1.4.1)

### 3.1 Header - Unified Metrics Bar
**Status:** ✅ Complete

```
┌──────────────────────────────────────────────────────┐
│ SOVEREIGN TERMINAL v1.4.1                            │
│ £12,500 | +£265 | MID_BULL | LIVE | 🏛️ Fortress OK  │
└──────────────────────────────────────────────────────┘
```

**Data Sources:**
- Total Wealth: `t212_portfolio.json` + `fortress_state.json`
- Session P/L: Calculated from position changes
- Market Phase: Gemini AI analysis (fallback: `MID_BULL`)
- Connectivity: Trading 212 API status

### 3.2 Sentinel Donut - Portfolio Balance
**Status:** ✅ Complete

**Colors:**
- Seed (Cash): `#fff7ed` (Ghost Whisper Orange)
- Harvest (Realized P/L): `#f0fdf4` (Mint Glow)

**Data:** `fortress_state.json`

### 3.3 Equity Curve - Historical Wealth
**Status:** ✅ Complete

**Chart Type:** Area chart with gradient fill  
**Color:** `#fff7ed` → transparent  
**Data:** `fortress_state.json.history`

### 3.4 Momentum Heatmap - Live Positions
**Status:** ✅ Complete (Anti-Sliver v1.4.1)

**Configuration:**
- Height: 600px (brute-force square bias)
- Stroke: 5px white dividers (`#f9fafb`)
- Color Ranges:
  - +3% and above: `#bbf7d0` (Mint Pastel)
  - +0.1% to +2.99%: `#f0fdf4` (Mint Tint)
  - -0.1% to -2.99%: `#fff1f2` (Rose Tint)
  - -3% and below: `#fecaca` (Rose Pastel)

**Data:** `t212_portfolio.json.positions`

### 3.5 Asset Mix Donut - Sector Allocation
**Status:** ✅ Complete

**Colors:** Whisper-tint palette (`#fff7ed`, `#f0fdf4`, etc.)  
**Data:** Calculated from `t212_portfolio.json`

### 3.6 Tactical Brief - AI Analysis
**Status:** ✅ Complete

**Content:**
- Market Phase assessment
- Limit entry suggestions (e.g., "MSFT @ $395.50")
- Strategic guidance text

**Data Source:** Gemini Pro API (fallback: static text)

### 3.7 Job C Sniper Command - ORB Trading
**Status:** 🚧 Phase 3 In Progress

**Current State:**
- [x] Dense table layout (8 columns)
- [x] Target Entry calculation: `ORB High + (0.1 × ATR)`
- [x] Stop Loss calculation: `ORB High - (1.5 × ATR)`
- [x] BUY button UI with `onclick` handler
- [ ] **Flask API endpoint** (planned)
- [ ] **Live execution** (planned)

**Columns:**
1. TICKER
2. STATUS (WATCHING, READY, ACTIVE)
3. ORB HIGH
4. TARGET ENTRY
5. STOP LOSS
6. RVOL
7. SIGNAL
8. ACTION (BUY button)

**Data:** Hardcoded `job_c_candidates` array (Phase 4: switch to yfinance)

---

## 4. Backend Services

### 4.1 Position Fetcher (`generate_isa_portfolio.py`)
**Status:** ✅ Complete

**Function:** Fetch Trading 212 positions and normalize UK prices  
**Output:** `t212_portfolio.json`

**Key Logic:**
```python
# UK stocks are returned in pence, normalize to pounds
if ticker.endswith('_UK_EQ'):
    price = price / 100
    value = value / 100
```

### 4.2 Fortress Module (`generate_static.py`)
**Status:** ✅ Complete

**Function:** Track realized P/L and cash balance  
**Output:** `fortress_state.json`

**State Schema:**
```json
{
  "total_wealth": 12500.00,
  "cash": 2500.00,
  "realized_pnl": 250.00,
  "history": [
    {"date": "2026-02-07", "pot_value": 2750.00}
  ]
}
```

### 4.3 Dashboard Generator (`generate_ui.py`)
**Status:** ✅ Complete, 🚧 Flask API Planned

**Current Function:** Render static HTML dashboard  
**Planned Enhancement:** Add Flask server with `/api/execute_trade` endpoint

**Data Flow:**
1. Load `t212_portfolio.json`
2. Load `fortress_state.json`
3. Call Gemini API for strategic brief
4. Populate `job_c_candidates` (currently hardcoded)
5. Render `templates/base.html` → `index.html`

### 4.4 Trading 212 API Client (`trading212_client.py`)
**Status:** ✅ Phase 2 Complete

**Functions:**
```python
class Trading212Client:
    def get_positions() -> List[Dict]
    def place_limit_order(ticker, quantity, limit_price, side) -> Dict
    def get_instrument_metadata(ticker) -> Dict
    def calculate_max_buy(ticker, cash, price) -> float
```

**Error Handling:**
- Exponential backoff for 429 rate limits
- Retry logic (3 attempts default)
- Authentication verification
- Request timeout (10s)

---

## 5. Data Sources & APIs

### 5.1 Trading 212 API
**Status:** ✅ Client Complete, 🚧 Live Integration Planned

**Endpoints Used:**
- `GET /api/v0/equity/positions` - Fetch open positions
- `GET /api/v0/equity/metadata/instruments` - Instrument limits
- `POST /api/v0/equity/orders` - Place orders (planned)

**Authentication:** API Key in environment variable `TRADING212_API_KEY`

**Rate Limiting:** Handled via exponential backoff

### 5.2 yfinance (Yahoo Finance)
**Status:** 📋 Phase 4 Planned

**Planned Usage:**
- Calculate ORB High (first 15 minutes of session)
- Calculate ATR (14-period rolling)
- Calculate Relative Volume (RVOL)
- Fetch current market prices

**Implementation:**
```python
import yfinance as yf

ticker = yf.Ticker('TSLA')
orb_high = calculate_orb_high(ticker)  # Custom function
atr = calculate_atr(ticker, period=14)
rvol = calculate_relative_volume(ticker)
```

### 5.3 Google Gemini Pro
**Status:** ✅ Complete (with fallback)

**Function:** Generate AI strategic brief  
**Fallback:** MID_BULL static text if API unavailable

**Prompt Template:**
```
Analyze the current portfolio and market conditions.
Provide tactical entry suggestions for Job A positions.
Current positions: {positions_summary}
```

---

## 6. Planned Features (Roadmap)

### Phase 3: Sniper Command Integration (Next)
**Target:** v1.5.0 - LIVE EXECUTION

- [ ] Add Flask server to `generate_ui.py`
- [ ] Create `/api/execute_trade` POST endpoint
- [ ] Wire BUY button to API endpoint
- [ ] Add toast notification system (CSS + JS)
- [ ] Implement audit trail logging (CSV file)

**Implementation Plan:** See [`implementation_plan.md`](file:///C:/Users/steve/.gemini/antigravity/brain/088e280b-50e2-4100-b142-eb2976f6cca8/implementation_plan.md)

### Phase 4: Live Data Integration
**Target:** v1.6.0

- [ ] Replace hardcoded `job_c_candidates` with yfinance data
- [ ] Calculate real-time ORB High, ATR, RVOL
- [ ] Auto-refresh sniper list every 2 minutes (14:30-21:00 GMT)
- [ ] Add market hours detection (NYSE/NASDAQ)

### Phase 5: Advanced Features
**Target:** v1.7.0+

- [ ] Stop loss tracking and alerts
- [ ] Position sizing calculator (risk % of portfolio)
- [ ] Trade performance analytics
- [ ] Telegram notifications for order fills
- [ ] Multi-timeframe ORB analysis (5m, 15m, 30m)

---

## 7. Security & Deployment

### 7.1 GitHub Secrets
**Storage:** Repository settings → Secrets and variables

**Configured Secrets:**
- `TRADING212_API_KEY` - Trading 212 authentication
- `GOOGLE_API_KEY` - Gemini Pro API access (optional)

### 7.2 Local Development
**Environment File:** `.env`

```bash
TRADING212_API_KEY=your_key_here
GOOGLE_API_KEY=your_gemini_key_here  # Optional
```

**Security Notes:**
- `.env` file is gitignored
- Never commit API keys to version control
- Use `.env.example` as template

### 7.3 Cloudflare Pages Deployment
**Status:** ✅ Active

**Build Command:** `python generate_ui.py`  
**Output Directory:** `.` (root, serves `index.html`)

**Trigger:** Push to `main` branch

**Limitations:**
- Static site only (no Flask server in production)
- Dashboard updates require regeneration + push

**Future:** Migrate to Cloudflare Workers for dynamic API endpoints

---

## 8. Design System (Ghost Sovereign v1.4.1)

### 8.1 Color Palette

**Primary Tints:**
```css
--industrial-orange: #fff7ed;  /* Ghost Whisper Orange */
--visible-mint: #f0fdf4;       /* Mint Glow */
--visible-rose: #fff1f2;       /* Rose Mist */
--ice-whisper: #eff6ff;        /* Ice Whisper Blue */
--lavender-dust: #f5f3ff;      /* Lavender Dust */
```

**Typography:**
```css
font-family: 'JetBrains Mono', monospace;
```

**Label Sizes:**
- Section Labels: 8px, uppercase, 0.1em letter-spacing
- Metrics: 9-11px
- Headers: 13-18px

### 8.2 Layout System

**Zero-Waste Floating Labels:**
```css
.chart-container {
    position: relative !important;
    padding-top: 0 !important;
}

.section-label {
    position: absolute !important;
    top: 8px !important;
    left: 12px !important;
    z-index: 100 !important;
    pointer-events: none;
}
```

**Grid Responsiveness:**
- Desktop: 2-column grid
- Mobile: Single column stack

---

## 9. Testing & Validation

### 9.1 API Client Tests
**Script:** `test_trading212.py`

**Test Coverage:**
- ✅ Authentication
- ✅ Position retrieval
- ✅ Instrument metadata
- ✅ Max buy calculation

**Run:** `python test_trading212.py`

### 9.2 UI Validation
**Manual Checklist:**
- [ ] Heatmap tiles are square (no slivers)
- [ ] Labels float inside containers (no vertical space)
- [ ] BUY buttons are clickable
- [ ] Colors match Ghost Sovereign palette
- [ ] Charts render without console errors

### 9.3 Browser Compatibility
**Tested:** Chrome, Edge (Chromium)  
**Known Issues:** None

---

## 10. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  SOVEREIGN SENTINEL                     │
│                    Data Pipeline                        │
└─────────────────────────────────────────────────────────┘

┌──────────────┐
│ Trading 212  │
│     API      │ ──┬─► get_positions() ──► t212_portfolio.json
└──────────────┘   │
                   └─► place_limit_order() (Phase 3)

┌──────────────┐
│  Sentinel    │
│     Pot      │ ──► track_realized_pnl() ──► fortress_state.json
└──────────────┘

┌──────────────┐
│   Gemini     │
│     Pro      │ ──► generate_strategic_brief() ──► ai_brief text
└──────────────┘

┌──────────────┐
│  yfinance    │
│ (Phase 4)    │ ──► calculate_orb_metrics() ──► job_c_candidates
└──────────────┘

         │
         ▼
┌──────────────┐
│ generate_ui  │ ──► Jinja2 Render ──► index.html
│     .py      │
└──────────────┘
         │
         ▼
    ┌────────────┐
    │  Browser   │ ◄─── User Clicks BUY Button
    └────────────┘
         │
         ▼ (Phase 3)
    POST /api/execute_trade
         │
         ▼
┌──────────────┐
│ trading212   │ ──► place_limit_order()
│  _client.py  │
└──────────────┘
```

---

## 11. Version History

| Version | Date | Description |
|---------|------|-------------|
| v1.3.1 | 2026-02-07 | Dense sniper list, whisper-tint palette |
| v1.4.0 | 2026-02-07 | BUY buttons, tactical brief, limit entries |
| v1.4.1 | 2026-02-07 | **CURRENT** - Hard CSS overrides, 600px heatmap, ghost orange |
| v1.5.0 | TBD | **PLANNED** - Live execution via Flask API |
| v1.6.0 | TBD | Live data integration (yfinance ORB/ATR) |

---

## 12. Performance Metrics

**Dashboard Load Time:** <2s (static HTML)  
**API Response Time:** ~500ms (Trading 212)  
**Chart Render Time:** <1s (ApexCharts)

**Data Update Frequency:**
- Current: Manual regeneration + push
- Planned (v1.5+): 2-minute auto-refresh during market hours

---

## 13. Support & Maintenance

**Repository:** `Dewsbex/sovereign-sentinel`  
**Documentation:** `docs/` directory  
**Issue Tracking:** GitHub Issues (private repo)

**Dependencies:**
- Python 3.x
- Jinja2 >= 3.1.2
- requests >= 2.31.0
- yfinance >= 0.2.35
- google-generativeai >= 0.3.0 (optional)

**Update Schedule:**
- Dashboard regeneration: On-demand (push to `main`)
- API schema updates: Monitor Trading 212 changelog
- Chart library: ApexCharts via CDN (auto-updates)
