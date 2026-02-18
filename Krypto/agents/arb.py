import asyncio
import logging
from .base import StrategyAgent
from shared.schemas import TradeSignal, MarketData, OrderSide, OrderType

logger = logging.getLogger("Arb_Agent")

class SpotFuturesArbAgent(StrategyAgent):
    """
    Monitors funding rates.
    If Funding > Threshold (e.g. 0.01% per 8h):
        Buy Spot, Short Futures (Delta Neutral).
    """
    def __init__(self):
        super().__init__(strategy_id="spot_futures_arb_v1", symbols=["BTC/USD", "BTC/USD:USD"]) # Spot and Perp
        self.funding_threshold = 0.0001 # 0.01%
        self.position_open = False
        self.entry_spread = 0.0

    async def on_tick(self, data: MarketData):
        # In a real system, we'd listen to a specific "FundingRate" channel
        # For MVP, we'll assume we poll funding in the run loop
        pass

    async def check_funding(self):
        # Mock funding check
        # real implementation: funding = await ccxt.fetch_funding_rate()
        funding_rate = 0.0002 # Mock positive funding
        
        if not self.position_open and funding_rate > self.funding_threshold:
            logger.info(f"High Funding Detected: {funding_rate}. Opening Arbitrage.")
            # Execute both legs simultaneously
            await self.send_order("BTC/USD", OrderSide.BUY, 0.5, "Arb Spot Leg")
            await self.send_order("BTC/USD:USD", OrderSide.SELL, 0.5, "Arb Futures Leg")
            self.position_open = True
            
        elif self.position_open and funding_rate < 0:
            logger.info("Funding turned negative. Closing Arbitrage.")
            await self.send_order("BTC/USD", OrderSide.SELL, 0.5, "Close Spot Leg")
            await self.send_order("BTC/USD:USD", OrderSide.BUY, 0.5, "Close Futures Leg")
            self.position_open = False

    async def run(self):
        while self.running:
            await self.check_funding()
            await asyncio.sleep(60) # Check every minute

if __name__ == "__main__":
    agent = SpotFuturesArbAgent()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(agent.start())
