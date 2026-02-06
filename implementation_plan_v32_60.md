# Implementation Plan: Sovereign Sentinel v32.60 Upgrade

## 1. Risk Logic (The "Scale Earned" Rule)
**Objective**: Shift from naive % allocation to Hard Seed + Merit-based scaling.
**Files**: `config/orb_config.json`, `sovereign_state_manager.py`

*   **Config**: Replace `trade_allocation_percent` with `seed_capital: 1000`.
*   **State Manager**:
    *   Initialize `scalper_cumulative_pnl` in `daily_performance`.
    *   Update `get_allocation_amount()`:
        *   Rule: `Allocation = £1000` (Base).
        *   Condition: `IF scalper_cumulative_pnl > 1000: Allocation = Total_Equity * 0.05`.

## 2. Execution Logic (Safety)
**Objective**: Prevent wicks/fakeouts and bad fills.
**Files**: `orb_execution.py`

*   **Candle Close**:
    *   Logic: Requires monitoring 5m candles.
    *   Impl: `if time % 300 == 0`: Check `close > range_high`.
*   **Slippage Audit**:
    *   Logic: Compare `Fill Price` vs `Trigger Price`.
    *   Action: If deviation > 0.2%, Immediate Market Close.
*   **Bracket Simulation**:
    *   Logic: Track `entry_price`.
    *   TP: `entry + (range * 2)`.
    *   SL: `range_low` (or mid-point).

## 3. Trend Bias (VWAP Guard)
**Objective**: Trade with the trend.
**Files**: `orb_observer.py`, `orb_execution.py`

*   **Observer**:
    *   Add `calculate_vwap(ticker)`.
    *   Store `vwap` in `market_conditions`.
*   **Execution**:
    *   Gate: `if price > vwap and signal == LONG: Fire`.

## 4. UI Refactoring (The Sovereign Look)
**Objective**: Mobile-first, cleaner data.
**Files**: `generate_static.py`

*   **Layout**: Vertical Stack (`flex-col`) instead of Grid.
*   **Heatmap**: 100% Width. Cells contain Ticker + % only.
*   **Donut**:
    *   Increase Radius by 25%.
    *   Leader Lines: SVG `line` elements to external labels.

## 5. Telemetry
**Objective**: Clear context.
**Files**: `orb_messenger.py`

*   **Prefix**: Check `os.getenv('ENV')`. Prepend `(DEMO)` or `(LIVE)`.

## 6. Persistence
**Objective**: Track the £1k Seed.
**Files**: `sovereign_state_manager.py`

*   **File**: `data/eod_balance.json` (New).
*   **Logic**: Append daily closing balance of the Scalper specifically.
