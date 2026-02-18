import asyncio
import logging
from .base import StrategyAgent
from shared.schemas import TradeSignal, MarketData, OrderSide, OrderType
from shared.alt_data_bridge import get_market_sentiment_score, get_crypto_fear_greed

logger = logging.getLogger("Sentiment_Agent")

class CrossProjectSentimentAgent(StrategyAgent):
    """
    Uses cross-project alternative data (Fear & Greed, Trends, News)
    to drive sentiment-based crypto trades.
    """
    def __init__(self):
        super().__init__(strategy_id="x_proj_sentiment_v1", symbols=["BTC/USD", "ETH/USD", "DOGE/USD"])
        self.sentiment_threshold_buy = 0.75  # High Greed -> Buy Momentum? Or Contrarian Sell?
        self.sentiment_threshold_sell = 0.25 # Extreme Fear -> Buy the Dip?
        # Let's assume Momentum Strategy for now:
        # High Sentiment -> Bullish (Buy)
        # Low Sentiment -> Bearish (Sell/Cash)

    async def check_alt_data(self):
        # 1. Get Synthesized Score (0.0 - 1.0)
        score = get_market_sentiment_score()
        
        # 2. Get Raw Fear & Greed for logging
        fg = get_crypto_fear_greed()
        fg_text = f"{fg.get('value', '?')} ({fg.get('sentiment', 'Unknown')})"
        
        logger.info(f"📊 Alt Data Scan | Score: {score:.2f} | FW&G: {fg_text}")

        # 3. Logic
        if score > self.sentiment_threshold_buy:
            logger.info(f"🚀 BULLISH Sentiment Spike ({score:.2f})!")
            # Example: Buy BTC
            await self.send_order("BTC/USD", OrderSide.BUY, 0.05, f"Sentiment Bullish {score:.2f}")
            await asyncio.sleep(600) # Cooldown

        elif score < self.sentiment_threshold_sell:
            logger.info(f"🐻 BEARISH Sentiment Dip ({score:.2f})!")
            # Example: Sell or Short
            # await self.send_order("BTC/USD", OrderSide.SELL, 0.05, f"Sentiment Bearish {score:.2f}")
            await asyncio.sleep(600) 

    async def on_tick(self, data: MarketData):
        pass # Not high-frequency price driven

    async def run(self):
        logger.info("Initializing Cross-Project Sentiment Agent...")
        logger.info("  Connected to: Alt Data Engine (via Shared Bridge)")
        
        while self.running:
            await self.check_alt_data()
            await asyncio.sleep(300) # Check every 5 minutes

if __name__ == "__main__":
    agent = CrossProjectSentimentAgent()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(agent.start())
