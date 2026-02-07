# Wealth Seeker v0.01

**Zero-Laptop Cloud-Native Autonomous Trading System**

## 🎯 Overview

Wealth Seeker is a fully autonomous trading system designed to operate entirely in the cloud via GitHub Actions. It combines deterministic decision logic with AI-powered research to execute two distinct strategies:

- **Job C (5% Autonomous)**: Opening Range Breakout (ORB) trading with VWAP filtering
- **Job A (95% Advisory)**: Strategic moat analysis for long-term investments

## 🔑 Required Secrets

Configure these in GitHub Repository Settings → Secrets:

| Secret Name | Purpose |
|-------------|---------|
| `T212_API_TRADE_KEY` | Trading212 API authentication |
| `T212_API_TRADE_SECRET` | Trading212 API secret |
| `ALPHA_VANTAGE_API_KEY` | Technical data via Alpha Vantage |
| `GOOGLE_API_KEY` | Gemini API for research & fact-checking |
| `TELEGRAM_TOKEN` | Bot authentication for notifications |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

## 📁 Project Structure

```
Sovereign-Sentinel/
├── .github/workflows/
│   └── seeker.yml              # Autonomous execution pipeline (14:25 UTC Mon-Fri)
├── data/
│   └── eod_balance.json        # State persistence (profits, scaling)
├── templates/
│   └── base.html               # Dashboard template
├── auditor.py                  # The Deterministic Gauntlet
├── sync_ledger.py              # T212 API integration
├── main_bot.py                 # Job C: ORB Strategy
├── strategic_moat.py           # Job A: Moat Analysis
├── generate_ui.py              # Static HTML generator
├── live_state.json             # Current state for UI
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Configure Secrets
Add all required secrets to your GitHub repository.

### 2. Test Locally (Optional)

```powershell
# Install dependencies
pip install -r requirements.txt

# Test T212 connection
python sync_ledger.py --test-connection

# Test auditor logic
python auditor.py

# Run bot in test mode (no real trades)
python main_bot.py --test-mode

# Generate dashboard
python generate_ui.py
```

### 3. Enable Automation

The GitHub Actions workflow automatically runs at **14:25 UTC Monday-Friday**. To trigger manually:
- Go to Actions → Wealth Seeker v0.01 → Run workflow

### 4. Deploy Dashboard

The workflow automatically commits the generated `index.html`. Configure Cloudflare Pages to deploy from your `main` branch.

## 🛡️ Safety Features

### The Deterministic Gauntlet (`auditor.py`)

Every trade passes through 5 hard-coded gates:

1. **Pence Normalization**: UK equities (`_UK_EQ` or `.L`) divided by 100
2. **Circuit Breaker**: Halts if daily drawdown ≥ £1,000
3. **Seed Lock**: Max £1,000 position until realized profit ≥ £1,000
4. **Scaling Gate**: Once unlocked, max position = 5% of total wealth
5. **Fact-Check Filter**: Gemini validates no dividend cuts, earnings surprises, or CEO changes

## 📊 Strategies

### Job C: The Wealth Seeker Sentinel (Autonomous)

**Opening Range Breakout (ORB)**
- Detects 5-minute candle breakout above opening range high
- Filters: Current price must exceed VWAP
- Executes market orders via T212 API
- Sends Telegram notifications

### Job A: The Strategic Fortress (Advisory)

**Moat Analysis Framework**
1. **ROIC vs WACC**: Must exceed by 2%+ for 5 years
2. **Gross Margin Stability**: Std dev < 2%
3. **Pricing Power**: Competitive landscape analysis

Outputs Telegram "Moat Dossier" with manual approval link.

## 📈 Dashboard Features

- **Sticky Header**: Total wealth, session P/L, T212 connectivity
- **Performance Heatmap**: ApexCharts treemap (emerald/crimson)
- **AI Strategic Brief**: Latest moat research findings
- **ORB Target Tracker**: Real-time candidate monitoring
- **Sector Allocation**: Donut chart with external labels

## ⚠️ Important Notes

- **Autonomous Trading**: Job C executes **real market orders** without human intervention
- **Circuit Breaker**: System halts at £1,000 daily drawdown
- **UK Equities**: All `.L` tickers automatically normalized (÷100)
- **Paper Trading**: Use `--test-mode` to validate logic before enabling autonomous mode

## 🔧 Manual Operations

```powershell
# Sync ledger manually
python sync_ledger.py

# Run moat analysis for a ticker
python strategic_moat.py AAPL

# Force dashboard regeneration
python generate_ui.py
```

## 📝 Version History

**v0.01 (Baseline)** - 2026-02-07
- Initial release
- ORB strategy with VWAP filtering
- Strategic moat analysis framework
- GitHub Actions automation
- Cloudflare Pages deployment

## 🤝 Support

This is an autonomous system. Monitor Telegram notifications and review the dashboard regularly.

**⚠️ USE AT YOUR OWN RISK. This system trades real money autonomously.**

---

**Wealth Seeker v0.01** | Human-Out-of-the-Loop Trading System
