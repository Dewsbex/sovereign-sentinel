"""
Sentiment Gate — Cross-project alternative data filter for Krypto.
Reads sentiment_snapshot.json produced by alt_data_engine.py (Sovereign-Sentinel).
Blocks trades during Extreme Fear / unfavourable market conditions.
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("SentimentGate")

# ─── Snapshot Paths ───
# alt_data_engine writes to Sovereign-Sentinel/data/sentiment_snapshot.json
SNAPSHOT_PATHS = [
    Path("/home/ubuntu/Sovereign-Sentinel/data/sentiment_snapshot.json"),       # VPS
    Path(r"C:\Users\steve\Sovereign-Sentinel\data\sentiment_snapshot.json"),    # Windows dev
    Path(__file__).parent.parent / "Sovereign-Sentinel" / "data" / "sentiment_snapshot.json",
]

# ─── Thresholds ───
# Fear & Greed: 0-100, where 0=Extreme Fear, 100=Extreme Greed
# Below FEAR_THRESHOLD → block trades (market panic)
# Above GREED_THRESHOLD → reduce position size (potential reversal)
FEAR_THRESHOLD = 20       # Block ALL trades below this
CAUTION_THRESHOLD = 35    # Reduce position size by 50%
GREED_THRESHOLD = 80      # Reduce position size by 25% (overextended)
MAX_SNAPSHOT_AGE_HOURS = 4


def _load_snapshot() -> dict:
    """Load the most recent sentiment snapshot."""
    for path in SNAPSHOT_PATHS:
        if path.exists():
            try:
                with open(path, 'r') as f:
                    snapshot = json.load(f)
                # Check freshness
                ts = snapshot.get("timestamp", "")
                if ts:
                    age = datetime.now() - datetime.fromisoformat(ts)
                    if age > timedelta(hours=MAX_SNAPSHOT_AGE_HOURS):
                        logger.warning(f"Sentiment snapshot is {age.total_seconds()/3600:.1f}h old (stale)")
                        return {}  # Stale data = no gate (fail open)
                return snapshot.get("data", {})
            except Exception as e:
                logger.error(f"Failed to read snapshot from {path}: {e}")
    logger.warning("No sentiment snapshot found — sentiment gate disabled (fail open)")
    return {}


def get_fear_greed_value() -> int:
    """Returns the crypto Fear & Greed index value (0-100), or -1 if unavailable."""
    data = _load_snapshot()
    fg = data.get("fear_and_greed", {})
    if fg and fg.get("value") is not None:
        try:
            return int(fg["value"])
        except (ValueError, TypeError):
            pass
    return -1


def get_crypto_headlines() -> list:
    """Returns latest CryptoPanic headlines for LLM context."""
    data = _load_snapshot()
    return data.get("cryptopanic", [])


def get_breaking_news() -> list:
    """Returns RSS breaking headlines for LLM context."""
    data = _load_snapshot()
    return data.get("rss_breaking", [])


def check_sentiment_gate() -> dict:
    """
    Main gate check. Returns:
    {
        "allowed": True/False,
        "position_scale": 1.0 (normal) / 0.5 (caution) / 0.75 (greed) / 0.0 (blocked),
        "fear_greed": 45,
        "reason": "..."
    }
    """
    fg_value = get_fear_greed_value()
    
    # No data → fail open (allow trade, don't block because data engine is down)
    if fg_value < 0:
        return {
            "allowed": True,
            "position_scale": 1.0,
            "fear_greed": -1,
            "reason": "Sentiment data unavailable — fail open"
        }
    
    # EXTREME FEAR: Block all trades
    if fg_value <= FEAR_THRESHOLD:
        logger.warning(f"SENTIMENT GATE BLOCKED: Extreme Fear ({fg_value}/100)")
        return {
            "allowed": False,
            "position_scale": 0.0,
            "fear_greed": fg_value,
            "reason": f"Extreme Fear ({fg_value}/100) — institutional capitulation risk"
        }
    
    # CAUTION ZONE: Reduce position size by 50%
    if fg_value <= CAUTION_THRESHOLD:
        logger.info(f"SENTIMENT GATE CAUTION: Fear zone ({fg_value}/100) — halving position")
        return {
            "allowed": True,
            "position_scale": 0.5,
            "fear_greed": fg_value,
            "reason": f"Fear zone ({fg_value}/100) — position size halved"
        }
    
    # EXTREME GREED: Slight reduction (market may be overextended)
    if fg_value >= GREED_THRESHOLD:
        logger.info(f"SENTIMENT GATE: Greed zone ({fg_value}/100) — slight position reduction")
        return {
            "allowed": True,
            "position_scale": 0.75,
            "fear_greed": fg_value,
            "reason": f"Greed zone ({fg_value}/100) — market may be overextended"
        }
    
    # NEUTRAL / COMFORTABLE ZONE
    return {
        "allowed": True,
        "position_scale": 1.0,
        "fear_greed": fg_value,
        "reason": f"Neutral sentiment ({fg_value}/100) — conditions favourable"
    }


if __name__ == "__main__":
    print("=== Sentiment Gate Test ===")
    result = check_sentiment_gate()
    print(f"Allowed: {result['allowed']}")
    print(f"Position Scale: {result['position_scale']}")
    print(f"Fear & Greed: {result['fear_greed']}")
    print(f"Reason: {result['reason']}")
    
    headlines = get_crypto_headlines()
    print(f"\nCrypto Headlines: {len(headlines)} items")
    for h in headlines[:3]:
        title = h.get("title", h) if isinstance(h, dict) else h
        print(f"  → {title}")
