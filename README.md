# SOVEREIGN SENTINEL v1.0

Autonomous Python Daemon and Portfolio Oracle.

## Setup
1. **Python**: Ensure Python 3.9+ is installed.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuration**:
   - Edit `.env` to update your Trading 212 API credentials
   - **IMPORTANT**: See [TRADING212_API_RULES.md](TRADING212_API_RULES.md) for authentication requirements
   - Edit `watchlist.json` to add your target buy prices.


## Running the System
Run the daemon and dashboard:
```bash
python sovereign_sentinel.py
```

- **Dashboard**: Access via [Live Deployment](https://sovereign-sentinel.pages.dev/) (Protected by Cloudflare Access)
- **Output**: The console will print "CRITICAL" or "PREPARING" alerts as they occur.

## Logic Core
- **Cash Hurdle**: Fails if `Net Yield + 2% Growth < 3.8%`.
- **Fat Pitch**: 
  - `EXECUTE` if Price <= Target Price.
  - `WATCH` if Price <= Target Price + 5%.
