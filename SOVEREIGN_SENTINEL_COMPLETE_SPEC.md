# Sovereign Sentinel: "Neon Sentry" (v2.1)
> **Codename:** NEON SENTRY  
> **Version:** 2.1 (Critical Stabilization)
> **Status:** BATTLE READY  
> **Last Updated:** 2026-02-10

---

## 1. System Manifesto
**Sovereign Sentinel** is an autonomous financial defense system designed to protect and grow capital through:
1.  **Iron Seed Protocol:** Strict risk capping (£1,000 max exposure) on experimental "Lab" trades.
2.  **Harmonic Intelligence:** `Gemini 2.5 Flash` grounded with real-time web search for non-hallucinogenic analysis.

### Core Philosophy (Neon Sentry)
- **Hybrid Delivery:** Static frontend on Cloudflare Pages; live API backend on Oracle VPS.
- **Real-Time Visibility:** Live Trading 212 API integration for instantaneous portfolio monitoring.
- **Spectrum Vision:** **Sector Census** logic separates "Main Holdings" (Strategic Core) from "Lab Experiments" (Seed).
- **Hardened Safety:** **Iron Seed Protocol** strictly caps experimental exposure at £1,000.
- **Cognitive Engine:** Powered by **Gemini 1.5 Flash** for rapid, low-hallucination market analysis.

---

## 2. Architecture & File Manifest

### 2.1 The "Sovereign Engine"
Unified logic for execution, analysis, and dashboard serving.

| File | Purpose | Key Capabilities |
|------|---------|------------------|
| `trading212_client.py` | **Hybrid Engine** | - Consolidated Logic<br>- **Master List Sync** (10k+ Instruments)<br>- Gemini 1.5 Flash + Grounding |
| `web/server.py` | **Dashboard Backend** | - Flask-based API<br>- Real-time Sector Calculation<br>- Tactical Brief Generation<br>- CORS enabled |
| `strategic_moat.py` | **The Strategist** | - **Sector Mapper** (Value-Weighted, Lab Filtered)<br>- Morning Brief Generation (09:00 UTC) |
| `main_bot.py` | **Job C Executor** | - US Market Scalper (14:25 UTC)<br>- **ORB Shield** (Time-Locked 14:25-21:05 UTC) |
| `auditor.py` | **The Gauntlet** | - **Iron Seed Enforcement** (<£1000 Lab Cap)<br>- Strict "Cash + Equity" Math |

### 2.2 Frontend (Cloudflare Pages)
- **Location**: `dist/` folder (local) -> `sovereign-sentinel.pages.dev` (live)
- **Framework**: Semantic HTML5, Vanilla JS, ApexCharts.
- **Config**: `dist/config.js` manages environment-aware API endpoints.

---

## 3. Data Integrity Layers

### 3.1 Master List Sync
- **Source**: Trading 212 API (`/equity/metadata/instruments`)
- **Storage**: `data/master_instruments.json`
- **Function**: Validates every target ticker before execution to prevent "ghost" orders.
- **Schedule**: Daily at 08:30 UTC.

### 3.2 Sector Census (The Lab Filter)
- **Logic**: Only positions with **Value > £250** are counted in Macro Sector Analysis.
- **Effect**: Prevents small "Seed" experiments from distorting the strategic portfolio view.
- **Component**: `SectorMapper` class in `strategic_moat.py`.

---

## 4. Operational Protocols

### 4.1 VPS Management (Skill: vps-management)
Updates to the live backend are managed via the `vps-management` skill:
- **Keys**: `C:\Users\steve\Sovereign-Sentinel\Stores\ssh-key-2026-02-08.key`
- **User**: `ubuntu@145.241.226.107`
- **Service**: `sovereign-web.service` (controlled via `systemctl`)

### 4.2 Spacetime Discipline
- **Morning Brief**: 09:00 UTC (Strategic Scan)
- **Market Open**: 14:30 UTC (US Session)
- **Hard Stop**: 21:05 UTC (Shield Deactivation)
- **Silence**: 21:05 - 14:25 UTC (No autonomous trading or spam)

---

## 5. The Iron Seed Protocol (Hardened)
The system strictly enforces a **£1,000 Max Exposure** limit for "Lab" trades (positions < £250).
- **Check**: `auditor.enforce_iron_seed()`
- **Action**: Blocks new entries if Lab Exposure ranges ≥ £1,000.
- **Goal**: Protects the "Harvest" (Realized Profit) from experimental erosion.

---

**[END OF SPECIFICATION v2.0.1]**
