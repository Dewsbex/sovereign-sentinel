# Sovereign Sentinel (ORB Engine) - Master System Specification (v32.50)

**HYBRID DUAL-MANDATE EDITION**
*This system implements a 95/5 Split Strategy: 95% Capital for Smart Investing (Fundamental), 5% for High-Risk Scalping (Technical).*

## 1. System Overview
**Name**: Sovereign Sentinel (Hybrid Engine)
**Version**: v32.60
**Architecture**: **Dual-Process**.
1.  **The Investor (95%)**: Daily Fundamental/Metric checks (Job A).
2.  **The Scalper (5%)**: Technical Breakout Simulation (Job C / Sentinel).

---

## 2. File Inventory & Status
**All modules are now Active or Designated for Re-integration.**

### 2.1 ✅ ACTIVE CORE (The Hybrid Stack)

| File | Role | Mandate | Status |
| :--- | :--- | :--- | :--- |
| `generate_isa_portfolio.py` | **Job A (The Investor)** | **95% Capital**. Manages Core Holdings using `oracle.py` logic. | **Active** |
| `main_bot.py` | **Job C (The Sentinel)** | **5% Capital**. Executes ORB Scalping logic on specific targets. | **Active** |
| `generate_static.py` | **Job B (The Artist)** | **Reporting**. Generates the Unified Dashboard. | **Active** |
| `oracle.py` | **The Brain (Fundamental)** | **Investing Logic**. Checks Yields, Moats, Cash Flow. | **Restoring** |
| `solar_cycle.py` | **The Clock (Macro)** | **Global Context**. Checks Tax Year, Macro Events. | **Restoring** |
| `immune_system.py` | **The Shield (Risk)** | **Global Safety**. Logic for "Falling Knife" & "Earnings Blackout". | **Restoring** |
| `config.py` | **Detailed Config** | **Active Legacy Support**. Required by `oracle.py` for variables. | **Active** |

### 2.2 🛠 UTILITIES & MAINTENANCE (Active Support)
*Helper scripts involved in Data Warehousing, Intelligence, and Debugging.*

| File | Category | Description | Status |
| :--- | :--- | :--- | :--- |
| `ledger_sync.py` | **Data Warehouse** | **Critical**. Fetches multi-year history, syncs Dividends/Fees to CSV/GDrive. | **Active** |
| `fetch_intelligence.py` | **Intelligence** | **SITREP Generator**. Fetches live news/prices for `generate_static.py`. | **Active** |
| `sniper_intelligence.py`| **Intelligence** | **Live Watchlist**. Independent scanner for `watchlist.json` targets. | **Active** |
| `golden_return.py` | **Math** | **Truth Engine**. Calculates Total Return (`Value - Net Deposits`). | **Active** |
| `total_ledger_performance.py` | **Math** | **History**. Summarizes all-time P/L from CSV history. | **Active** |
| `inject_ledger_metrics.py`| **Data** | **Injector**. Merges CSV data into JSON cache. | **Active** |
| `utils.py` | **Helper** | Common string formatting and math functions. | **Active** |
| `global_normalization.py` | **Helper** | Standalone script to normalize pence/pounds in `data`. | **Active (Manual)** |
| `activate_live.py` | **Ops** | Script to switch environment modes. | **Active (Manual)** |
| `fix_v30.py` | **Maintenance** | Emergency patch script (Legacy/Active). | **Active** |
| `analyze_discrepancy.py` | **Debug** | Tool to find mismatches between T212 and Local Ledger. | **Dev Tool** |
| `fetch_ledger.py` | **Debug** | standalone ledger fetcher. | **Dev Tool** |
| `check_ledger.py` | **Debug** | Simple consistency check. | **Dev Tool** |

### 2.1.1 ⚙️ ORB COMPONENTS (The Scalper Engine)
*Modular components imported by `main_bot.py` to execute Job C.*

| File | Role | Description |
| :--- | :--- | :--- |
| `sovereign_state_manager.py` | **State** | Manages `ledger_state.json` and `eod_balance.json` (Scalper Ledger). |
| `orb_observer.py` | **Eyes** | Analyzes market conditions (RVOL, Gap) during observation window. |
| `orb_execution.py` | **Hands** | Handles order logic, entry triggers, and position management. |
| `orb_shield.py` | **Defense** | Risk management wrapper (Max Drawdown, Circuit Breakers). |
| `orb_messenger.py` | **Voice** | Handles Telegram/Discord notifications with **Environment Prefixing** `(DEMO)`/`(LIVE)`. |

### 2.3 🧪 VERIFICATION & TESTING
*Files used for CI/CD and Logic Verification.*

| Group | Files | Description |
| :--- | :--- | :--- |
| **Unit Tests** | `test_*.py` (15 files) | Local logic tests (`test_limit_order.py`, `test_orb_flow.py`, etc.). |
| **Verification** | `verify_*.py` (5 files) | Live/Mock environment verifiers (`verify_live_trade.py`, `verify_keys.py`). |
| **Inspection** | `inspect_*.py` (3 files) | API Schema inspectors (`inspect_t212_full.py`). |
| **Debug Logs** | `debug_*.py`, `.log` files | Transient debug scripts and log outputs. |

### 2.4 ❌ ARCHIVED / DEPRECATED (Do Not Replicate)
*Legacy files from previous architectures (v27/v29). Preserved for reference but NOT used.*

| File | Former Role | Reason for Abandonment |
| :--- | :--- | :--- |
| `sovereign_sentinel.py` | **Daemon API** | Replaced by `main_bot.py` (Cron Architecture). |
| `sentinel_daemon.py` | Daemon Logic | Obsolete v29 Logic. |
| `sovereign_architect.py` | Setup Script | Obsolete v27 Setup. |
| `orb_sidecar.py` | Helper | Merged into `main_bot.py`. |
| `reset_orb_data.py` | Utility | Dangerous/Obsolete manual reset. |
| `.github/workflows/sentinel-daemon.yml` | Workflow | Replaced by `deployment.yml`. |
| `.github/workflows/orb-autonomous.yml` | Workflow | Replaced by `deployment.yml`. |
| `T212_Script_Spec.txt` | Spec | Old reference text. |
| `FUNCTIONALITY_GAP_ANALYSIS.md` | Doc | Superseded by this Spec. |

> **Audit Note**: Any file in the root directory NOT listed above is considered **Transient/Temporary** (e.g., `scan_output.txt`, `runs.json`).

---

## 3. Operational Logic (The Dual Mandate)

### 3.1 Mandate A: The Smart Investor (95% Equity)
**Process**: `generate_isa_portfolio.py` (Job A)
**Frequency**: Daily (End of Day or Morning Prep).
**Logic**:
1.  **Audits Portfolio**: Fetches T212 Holdings.
2.  **Applies Oracle**: Calls `oracle.run_full_audit(ticker)` on every holding.
    - *Checks*: Dividend Yield > Risk Free Rate? Management Buying?
3.  **Applies Solar Cycle**: Checks `solar_cycle.phase_4b_tax_logic_fork()` (ISA vs GIA).
4.  **Rebalancing**: Generates "TRIM" or "ADD" signals in `ledger_state.json` based on Fundamental Health.
### 3.2 Mandate B: The Scalper (5% Equity)
**Process**: `main_bot.py` (Job C)
**Frequency**: Cron Trigger (14:25 UTC).
**Logic**:
1.  **Budget Constraint**: "The Seed Rule". Starts with **£1,000 Hard Cap**. 
    - *Scaling*: Unlocks 5% of Total Equity ONLY after Scalper Profit > £1,000.
2.  **Strategy**: Technical ORB (Opening Range Breakout) with **Trend Bias**.
    - **VWAP Guard**: Longs only if Price > VWAP.
    - **Candle Close**: Entries trigger on 5m Candle Close (No premature wicks).
3.  **Safety**:
    - **Slippage Audit**: Immediate Exit if Fill vs Trigger > 0.2%.
    - **Immune System**: Must check `immune.check_earnings_radar()` before trading.
    - **Circuit Breaker**: If `current_session_loss >= 1000.00`, set `Job_C_Status = DISABLED`.

### 3.3 Mandate C: The Artist (UI & Reporting)
**Process**: `generate_static.py` (Job B)
**Desired State (v32.60)**:
1.  **Layout**: "Sovereign Stack". Vertical Flex Column for Mobile-First focus.
2.  **Asset Donut**:
    - **Dimensions**: Enlarged (radius=90).
    - **Labels**: SVG Leader Lines connecting segments to external labels (Ticker + %).
3.  **Heatmap**: Full-width (100%) expansion, Ticker-only labels for density. 18pt font.
4.  **Target Tracker**: Row height increased by 15%.
5.  **Telemetry**:
    - **Prefix**: All notifications must carry `(DEMO)` or `(LIVE)`.
    - **EOD Report**: 21:00 GMT Summary of the independent £1k Seed Growth (`eod_balance.json`).
    - **Normalization**: UK Equities hard-locked to divide by 100.

### 3.4 Mandate D: The Commander (Manual API Hub)
**Interface**: "Settings Cog" Modal in Dashboard.
**Functions**:
1.  **Sync Metadata**: Trigger `GET /api/v0/equity/metadata/instruments`.
2.  **Panic Sell**: Ticker Input + "Sell All" Button -> Immediate Market Exit.
3.  **Mode Switch**: Toggle `(DEMO)` / `(LIVE)` (Requires Token Validation).

---

## 4. Integration Plan (Replication Steps)
To build the Hybrid System:

1.  **Deploy Core**: All files in Section 2.1.
2.  **Configure Split**:
    - In `orb_config.json`: Set `"seed_capital": 1000.0`.
    - In `config.py`: Ensure `RISK_FREE_RATE` and `TAX_VARS` are correct for Oracle.
3.  **Run Pipeline**:
    - **Step 1 (Investor)**: `python generate_isa_portfolio.py` -> Runs Oracle, Updates Core DB.
    - **Step 2 (Reporter)**: `python generate_static.py` -> Visualizes Health.
    - **Step 3 (Scalper)**: `python main_bot.py` -> Trades the 5% Budget using Technicals.

---

## 5. Automation
**Workflow**: `.github/workflows/deployment.yml`
- **Schedule**: `25 14 * * 1-5`.
- **Job Chain**:
    1.  `Run Investor Audit` (Job A)
    2.  `Run Scalper` (Job C) - *Dependent on Job A Success*.
    3.  `Generate Report` (Job B) - *Final State*.
