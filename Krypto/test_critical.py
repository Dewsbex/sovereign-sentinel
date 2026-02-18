import asyncio
import logging
import sys
from manager.normalization import Normalizer
from manager.ratelimit import DecayingTokenBucket

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test")

async def test_normalization():
    logger.info("--- Testing Normalization ---")
    
    # Test 1: BTC/USD Amount (8 decimals)
    raw_amount = 0.123456789
    norm_amount = Normalizer.normalize_amount("BTC/USD", raw_amount)
    logger.info(f"BTC Amount: {raw_amount} -> {norm_amount} (Expected 0.12345678)")
    assert norm_amount == 0.12345678, "BTC Amount failed"

    # Test 2: DOGE/USD Amount (0 decimals)
    raw_doge = 100.9
    norm_doge = Normalizer.normalize_amount("DOGE/USD", raw_doge)
    logger.info(f"DOGE Amount: {raw_doge} -> {norm_doge} (Expected 100.0)")
    assert norm_doge == 100.0, "DOGE Amount failed"

    # Test 3: GBP Balance (The Pence Bug)
    raw_gbp = 100.55999999999999
    fixed_gbp = Normalizer.fix_pence_bug(raw_gbp, "GBP")
    logger.info(f"GBP Balance: {raw_gbp} -> {fixed_gbp} (Expected 100.55)")
    assert fixed_gbp == 100.55, "GBP Fix failed"
    
    logger.info("✅ Normalization Tests Passed")

async def test_rate_limit():
    logger.info("--- Testing Rate Limit Decay ---")
    
    # Tiny bucket: Capacity 2, Decay 1/sec
    bucket = DecayingTokenBucket(capacity=2, decay_rate=1.0)
    
    # Burst 2 requests (Should pass)
    assert await bucket.consume(1) == True
    assert await bucket.consume(1) == True
    logger.info("Burst 2/2 passed")
    
    # 3rd request should fail immediately
    assert await bucket.consume(1) == False
    logger.info("3rd request rejected (Correct)")
    
    # Wait 1.1s (Decay 1.1 points -> Refill 1 token)
    logger.info("Waiting for decay...")
    await asyncio.sleep(1.1)
    
    # 4th request should pass
    assert await bucket.consume(1) == True
    logger.info("4th request passed after decay")
    
    logger.info("✅ Rate Limit Tests Passed")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(test_normalization())
        loop.run_until_complete(test_rate_limit())
    except KeyboardInterrupt:
        pass
