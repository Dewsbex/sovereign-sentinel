# Sovereign Sentinel (ORB Engine) - Master System Specification (v32.47)

**CODEBASE REALITY EDITION**
*This document reflects the exact state of the codebase as of v32.47. Discrepancies have been resolved in favor of the actual code.*

## 1. System Overview
**Name**: Sovereign Sentinel (ORB Engine)
**Version**: v32.47 (Active Codebase)
**Architecture**: **Cron-Based Simulation Loop** (Active) vs **FastAPI Daemon** (Legacy/Deprecated).
**Broker API**: Trading 212 API v0 (REST).

---

## 2. File Inventory & Status
Every file in the repository has been audited and categorized.

### 2.1 ✅ ACTIVE CORE (The "Sovereign Finality" Stack)
*Replicate these files to build the v32.25 system.*

| File | Role | Dependencies |
| :--- | :--- | :--- |
| `main_bot.py` | **Entry Point**. Runs the logic loop. | `orb_*.py`, `sovereign_state_manager.py` |
| `orb_execution.py` | **Execution Engine**. Limit/Market Logic. | `config/orb_config.json` |
| `orb_shield.py` | **Protection**. Stop/Limit Logic. | `t212_api` |
| `orb_observer.py` | **Market Data**. RVOL Calculation. | `yfinance`, `config/orb_config.json` |
| `orb_messenger.py` | **Notifications**. Telegram Bot. | `requests` |
| `sovereign_state_manager.py` | **State**. Manages `ledger_state.json`. | `json`, `os` |
| `generate_isa_portfolio.py` | **Job A (Auditor)**. Syncs T212 Data. | `yfinance`, `requests` |
| `generate_static.py` | **Job B (Artist)**. Generates UI. | `jinja2`, `utils.py` |
| `templates/base.html` | **UI Template**. Tailwind + CSS Animations. | N/A |
| `utils.py` | **Helper**. Formatting/Truncation. | N/A |
| `config/orb_config.json` | **Config**. Strategy Parameters. | N/A |
| `data/ledger_state.json` | **Database**. Persistent State. | N/A |

### 2.2 ❌ ARCHIVED / LOST FUNCTIONALITY (Do Not Replicate)
*The following files belong to the Legacy "Sovereign Architect" (v27). They are deprecated, but contain **significant functionality** that is **NOT** present in the active v32 System. Replicating the active system WILL result in the loss of these features.*

| File | Status | **LOST FUNCTIONALITY** (Gap Analysis) |
| :--- | :--- | :--- |
| `sovereign_sentinel.py` | **Abandoned** | **The Daemon**: Continuous loop, 15-minute polling, and FastAPI Dashboard. *Active system is a 5-minute cron job.* |
| `oracle.py` | **Abandoned** | **Fundamental Analysis**: Dividend Yield checks, Moat analysis, Insider Trading scans. *Active system is Purely Technical (Price Action).* |
| `solar_cycle.py` | **Abandoned** | **Macro & Tax Logic**: pre-market Futures checks, "Transatlantic Pivot" (Macro data lock), and **ISA/GIA Tax Logic** (Bed & Breakfast rules). |
| `immune_system.py` | **Abandoned** | **Advanced Risk**: "Earnings Radar" (Block buy <7 days to earnings), "Falling Knife" protection, and Split Guard. *Active system checks only Price.* |
| `config.py` | **Abandoned** | **Complex Config**: Variables for Stamp Duty, FX Friction, and Tax Drag. *Active config is simplified.* |

> **CRITICAL WARNING**: The "Active" v32 system is a **Technical Scalper**. The "Legacy" v27 system was a **Fundamental Investor**. If your goal is *Investing*, v32 is a functional regression.

---

## 3. Operational Logic (Code Truth)

### 3.1 The Sentinel Loop (`main_bot.py`)
- **Mode**: **Simulation Burst**.
- **Duration**: **300 Seconds** (5 Minutes).
- **Trigger**: GitHub Actions Cron (`deployment.yml`).
- **Logic**:
    1.  **Init**: Loads State & Config. Checks Circuit Breaker.
    2.  **Observe**: Runs `ORBObserver`. (Note: Result currently unused in loop).
    3.  **Execute**: Loops for 5 mins. Calls `engine.fetch_current_price(ticker)`.
    4.  **Shutdown**: Saves State. Commits to Git.

### 3.2 Execution Realities (`orb_execution.py`)
- **Price Feed**: `fetch_current_price()` returns **`0.0` (Hardcoded Mock)**.
    - *Implication*: The bot cannot trade in its current state without a Price Source update.
- **Entry Logic**: `if current_price >= r['trigger_long']`.
- **Order Type**: Market Order (Synthetic Limit).

### 3.3 Shield Logic (`orb_shield.py`)
- **Target Calculation**: `Entry Price + (Range * 2.0)`.
- **Stop Calculation**: `Range Low`.
- **TimeValidity**: `"DAY"` (Hardcoded).

### 3.4 Intelligence Source
- **Fact**: `main_bot.py` does **NOT** generate `orb_intel.json`.
- **Source**: `orb_intel.json` must be provided manually or by a separate script (`fetch_intelligence.py` exists but is standalone).

---

## 4. Configuration Schema (Active)
**File**: `config/orb_config.json` (NOT `config.py`)

```json
{
    "risk": {
        "initial_capital": 1000.0,
        "max_drawdown_percent": 10.0,
        "trade_allocation_percent": 35.0,
        "min_range_percent": 0.8
    },
    "filters": { "min_rvol": 1.5, "index_ticker": "SPY" },
    "watchlist": ["TSLA", "NVDA", "AMD", "PLTR", "COIN", "MARA", "MSTR", "NUE", "DHR"]
}
```

---

## 5. Automation (GitHub Actions)
**Active Workflow**: `.github/workflows/deployment.yml`

- **Schedule**: `25 14 * * 1-5`.
- **Env Secrets**: `T212_API_KEY`, `T212_API_SECRET`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`.
- **Permissions**: `contents: write`.

---

## 6. How to Replicate (The Only Way)
1.  **Ignore** all files in Section 2.2.
2.  **Deploy** files in Section 2.1.
3.  **Configure** `orb_config.json`.
4.  **Run Sequence**:
    - `python generate_isa_portfolio.py` (Job A)
    - `python generate_static.py` (Job B)
    - `python main_bot.py` (The Sentinel)
