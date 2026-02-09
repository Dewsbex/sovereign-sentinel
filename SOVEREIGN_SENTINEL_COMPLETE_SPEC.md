# Sovereign Sentinel - Complete System Specification (v1.9.6)

**Version:** v1.9.6 (IRON SEED PROTOCOL)
**Status:** PRODUCTION / LIVE
**Last Updated:** 2026-02-09
**Codename:** Proving Ground

---

## 1. System Overview

**Sovereign Sentinel** is a consolidated, high-integrity autonomous trading system running on an Oracle VPS. It implements a "Hybrid Engine" architecture where a single client handles Trading 212 execution, Gemini 2.5 AI analysis, and Telegram alerting.

### Core Philosophy (v1.9.6)
- **Consolidation:** All logic resides in `Sovereign-Sentinel/`.
- **Integrity:** "Watchdog" architecture requires 3 layers of pre-flight checks.
- **Grounding:** AI decisions are backed by Google Search (Gemini 2.5 Flash).
- **Hard-Lock Auth:** 37-character API keys are strictly enforced.
- **Capital Philosophy:** The Autonomous Engine (Job C) operates on a strict "Proving Ground" model. It is restricted to a fixed Seed Capital (£1,000) until it proves viability by generating £1,000 in Net Profit.

---

## 2. Architecture & File Manifest

### 2.1 The "Hybrid Engine"
The system logic is unified into a single robust client.

| File | Purpose | Key Capabilities |
|------|---------|------------------|
| `trading212_client.py` | **Hybrid Engine** | - Consolidated Logic (formerly `build_client.py`)<br>- Native Telegram (`send_telegram`)<br>- Gemini 2.5 Flash + Grounding<br>- T212 API Execution |
| `main_bot.py` | **Job C Executor** | - US Market Scalper (14:25 UTC)<br>- Zombie Recovery (Alpha Vantage)<br>- Imports `Trading212Client` |
| `auditor.py` | **The Gauntlet** | - Risk limits & Logic gates<br>- Uses `Trading212Client` for data |
| `strategic_moat.py` | **Job A Advisor** | - Moat Research<br>- Uses `Trading212Client` for AI & Alerts |
| `dashboard.py` | **Visual Command Center** | - Read-Only monitoring<br>- Seed vs. Profit tracking<br>- Hosted via Cloudflare Tunnel |

### 2.2 The "Sentry" Layer
New files introduced in v1.9.5 for system integrity.

| File | Purpose | Schedule |
|------|---------|----------|
| `watchdog.py` | **Integrity Sentry** | **07:55 UTC**<br>- Verifies existence of all critical files<br>- Fallback raw-request alerting |
| `monday_preflight.py` | **Diagnostic Tool** | **08:01 UTC** & **14:31 UTC**<br>- Checks Cash, Auth, & P/L<br>- Direct-to-Telegram Reporting |

---

## 3. Chronobiology: The 4-Stage Heartbeat

The system operates on a strict 4-stage daily rhythm (Monday-Friday), managed via `crontab`.

### Stage 1: Integrity Scan (07:55 UTC)
- **Script:** `watchdog.py`
- **Goal:** Verify "Battle Ready" state.
- **Fail Mechanism:** Immediate Telegram PANIC alert if any file (`main_bot.py`, `client`, etc.) is missing.

### Stage 2: Pre-Flight (08:01 UTC)
- **Script:** `monday_preflight.py`
- **Goal:** London Open Checks.
- **Actions:** Verify API connection, report Cash/Equity/P&L.

### Stage 3: Execution (14:25 UTC)
- **Script:** `main_bot.py --live`
- **Goal:** US Market Open Scalping (Job C).
- **Actions:** 
    1. Check `emergency.lock`
    2. Check Alpha Vantage Data (Zombie Recovery if needed)
    3. Execute ORB Strategy
    4. Verify via Auditor

### Stage 4: Post-Flight (14:31 UTC)
- **Script:** `monday_preflight.py --postflight`
- **Goal:** Confirm bot started successfully and report initial status.

---

## 4. Authentication & Security

### 4.1 Schema Hardening
Old variables (e.g., `T212_API_TRADE_KEY`) are **DEPRECATED**.

| Variable | Format | Purpose |
|----------|--------|---------|
| `TRADING212_API_KEY` | 37-characters | **CRITICAL**: Execution & Data |
| `ALPHA_VANTAGE_API_KEY` | Alphanumeric | **REQUIRED**: Zombie Recovery Data |
| `GOOGLE_API_KEY` | Alphanumeric | Gemini 2.5 Flash (AI Analysis) |
| `TELEGRAM_TOKEN` | Bot Token | Alerts & Reporting |
| `TELEGRAM_CHAT_ID` | Integer | Alert Recipient |

### 4.2 Circuit Breakers
- **Lock File:** `data/emergency.lock`
- **Logic:** If present, `main_bot.py` aborts immediately.
- **Auditor:** Hard stop at £1,000 drawdown.

---

## 5. AI Specification

- **Model:** `gemini-2.5-flash`
- **Endpoint:** `v1beta`
- **Grounding:** `{"tools": [{"google_search": {}}]}`
- **Usage:**
    - `strategic_moat.py`: Deep Research, Fact Checking, Moat Analysis.
    - `auditor.py`: News sentiment validation for "The Gauntlet".

---

## 6. Deployment Status (Oracle VPS)

- **OS:** Oracle Linux (ARM64) confirmed.
- **Python:** v3.x
- **Location:** `/home/ubuntu/Sovereign-Sentinel`
- **Dependencies:** `requests`, `yfinance`, `google-generativeai` (legacy support), `tenacity`.
- **State:** **OPERATIONAL**

---

## 7. Internal Logic Protocols (Granular)

### 7.1 Strategic Moat (v1.9.4 Spec)
The Advisory Engine (`strategic_moat.py`) enforces 4 strict protocols:
1.  **Ticker Hallucination Guard**: Requires **≥90% fuzzy match** between user input and `instruments.json` company name to prevent "VTRS vs VITL" errors.
2.  **Step-Lock Protocol**: Research Plan MUST be written to `data/research_plans/{ticker}_plan.md` *before* AI analysis begins. Write failure = Abort.
3.  **Sector Quant Lock**:
    *   **REITs**: Must use Price/AFFO. P/E is Forbidden.
    *   **Pharma**: Must include TAM (Total Addressable Market) and Pipeline analysis.
4.  **Short-Seller Debate**: The AI generates a Bear Case, then attempts to refute it with data. **≥3/5 arguments** must be refuted to sustain a BUY rating.

### 7.2 Zombie Recovery (Job C)
The Scalper (`main_bot.py`) includes resilience for Alpha Vantage data outages:
*   **Retry Loop**: Checks for data every **60 seconds**.
*   **Stale Cutoff:** **15:15 UTC**. If data returns after this time, the bot logs a "Theoretical Signal" but does **NOT** trade.
*   **Retrospective ORB**: If data returns before cutoff, it reconstructs the 14:30-14:45 range from 1-minute bars.

### 7.3 The Iron Seed Protocol
*   **Rule Name**: "The Iron Seed Protocol"
*   **Constraint**: Job C Total Allocation is **HARD-CAPPED at £1,000**.
*   **The Lock**: The system cannot exceed £1,000 exposure regardless of Total Wealth.
*   **The Key**: Scaling is **ONLY** permitted after the bot achieves £1,000 in Realized Profit. At that point, the Human Pilot determines the new allocation (up to 100%) via manual config update.
*   **Enforcement**: `auditor.py` rejects any trade that would push Job C exposure beyond the £1,000 ceiling until the profit threshold is met.

---

## 8. Visual Management

### 8.1 Dashboard Requirements

The **Dashboard** (`dashboard.py`) provides a read-only visual interface for monitoring the Proving Ground progress.

**Hosting:**
- Deployed on Oracle VPS
- Accessible via Cloudflare Tunnel

**Key Metrics Displayed:**
- **Seed Utilized**: Current capital deployed by Job C (out of £1,000 maximum)
- **Realized Profit Progress**: Net profit tracking toward the £1,000 unlock target
- **Moat Holdings**: Current strategic positions (Job A)

**Design Principles:**
- Read-only (no execution controls)
- Real-time data sync from `live_state.json`
- Clear visual distinction between Seed operations (Job C) and Moat positions (Job A)

---

**[END OF SPECIFICATION v1.9.6]**
