"""
Alt Data Bridge — Cross-project alternative data consumer.
Reads sentiment_snapshot.json produced by alt_data_engine.py.
Provides normalized signals for any project (Sentinel, Krypto, etc.).
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("AltDataBridge")

# Snapshot location (relative to Sovereign-Sentinel root)
# alt_data_engine writes to data/sentiment_snapshot.json
SNAPSHOT_PATHS = [
    Path(__file__).parent.parent / "data" / "sentiment_snapshot.json",       # From shared/ -> ../data/
    Path("/home/ubuntu/Sovereign-Sentinel/data/sentiment_snapshot.json"),    # VPS absolute
    Path(r"C:\Users\steve\Sovereign-Sentinel\data\sentiment_snapshot.json"), # Windows dev
]


def _load_snapshot() -> dict:
    """Load the most recent sentiment snapshot from SQLite."""
    import sqlite3
    # Look for the DB in the main Sovereign-Sentinel project since this is a shared script that might run elsewhere
    db_path = Path(r"C:\Users\steve\Sovereign-Sentinel\shared\data\audit_trail.db")
    if not db_path.exists():
        # Fallback to relative path if not found, though unlikely given hardcoded paths above
        db_path = Path(__file__).parent.parent.parent / "Sovereign-Sentinel" / "shared" / "data" / "audit_trail.db"
        if not db_path.exists():
            logger.warning(f"No audit_trail.db found at {db_path}")
            return {}
            
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        row = c.execute("SELECT timestamp, data FROM sentiment_snapshots ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        
        if row:
            ts, data_str = row
            # Check freshness (< 2 hours old)
            if ts:
                age = datetime.now() - datetime.fromisoformat(ts)
                if age > timedelta(hours=2):
                    logger.warning(f"Snapshot is {age.total_seconds()/3600:.1f}h old (stale)")
            return json.loads(data_str)
    except Exception as e:
        logger.error(f"Failed to read snapshot from SQLite {db_path}: {e}")
        
    logger.warning("No sentiment snapshot found in database")
    return {}


def get_crypto_fear_greed() -> dict:
    """
    Returns crypto Fear & Greed Index.
    Output: {"value": "72", "sentiment": "Greed"} or empty dict.
    """
    data = _load_snapshot()
    return data.get("fear_and_greed", {})


def get_crypto_news() -> list:
    """
    Returns latest CryptoPanic headlines.
    Output: List of news items or empty list.
    """
    data = _load_snapshot()
    return data.get("cryptopanic", [])


def get_market_sentiment_score() -> float:
    """
    Synthesizes a 0.0–1.0 sentiment score from available alt data.
    0.0 = Extreme Fear, 1.0 = Extreme Greed.
    Falls back to 0.5 (neutral) if no data available.
    """
    data = _load_snapshot()
    if not data:
        return 0.5

    score = 0.5
    signals = 0

    # Fear & Greed (0-100 scale -> 0.0-1.0)
    fg = data.get("fear_and_greed", {})
    if fg and fg.get("value") is not None:
        try:
            score = int(fg["value"]) / 100.0
            signals += 1
        except (ValueError, TypeError):
            pass

    # Google Trends: "market crash" searches inversely correlate with sentiment
    trends = data.get("pytrends", {})
    if trends and isinstance(trends, dict):
        crash_interest = trends.get("market crash", 0)
        dip_interest = trends.get("buy the dip", 0)
        if crash_interest > 0 or dip_interest > 0:
            # High "market crash" = fear, high "buy the dip" = greed
            trend_score = dip_interest / max(crash_interest + dip_interest, 1)
            score = (score * signals + trend_score) / (signals + 1)
            signals += 1

    return round(min(max(score, 0.0), 1.0), 3)


def get_macro_fed_rate() -> dict:
    """Returns latest Federal Funds Rate data."""
    data = _load_snapshot()
    return data.get("macro_data", {})


def get_breaking_headlines() -> list:
    """Returns RSS headlines from major financial news."""
    data = _load_snapshot()
    return data.get("rss_breaking", [])


if __name__ == "__main__":
    print("=== Alt Data Bridge Test ===")
    print(f"Sentiment Score: {get_market_sentiment_score()}")
    print(f"Fear & Greed: {get_crypto_fear_greed()}")
    print(f"Crypto News: {len(get_crypto_news())} items")
    print(f"Fed Rate: {get_macro_fed_rate()}")
    print(f"Headlines: {len(get_breaking_headlines())} items")
