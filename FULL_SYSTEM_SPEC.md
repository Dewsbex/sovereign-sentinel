# Sovereign Sentinel (ORB Engine) - Master System Specification (v32.50)

**HYBRID DUAL-MANDATE EDITION**
*This system implements a 95/5 Split Strategy: 95% Capital for Smart Investing (Fundamental), 5% for High-Risk Scalping (Technical).*

## 1. System Overview
**Name**: Sovereign Sentinel (Hybrid Engine)
**Version**: v32.50
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
| `config.py` | **Detailed Config** | **Legacy Settings**. Contains Tax/Macro vars needed by Oracle. | **Partial** |

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
1.  **Budget Constraint**: `Allocated Capital = Total Net Equity * 0.05`.
2.  **Strategy**: Technical ORB (Opening Range Breakout).
3.  **Constraints**:
    - **Immune System**: Must check `immune.check_earnings_radar()` before trading.
    - **Oracle Check**: Ideally only scalps tickers that pass a basic "Quality" filter (optional).

---

## 4. Integration Plan (Replication Steps)
To build the Hybrid System:

1.  **Deploy Core**: All files in Section 2.1.
2.  **Configure Split**:
    - In `orb_config.json`: Set `"trade_allocation_percent": 5.0` (Scalper uses 5% of Total).
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

---

## 6. Deprecated (Truly Unused)
- `sovereign_sentinel.py` (The old Daemon Loop).
- `sentinel_daemon.py` (Old Logic).
- `orb_sidecar.py`.
