import asyncio
import logging
from .base import StrategyAgent
from shared.schemas import TradeSignal, MarketData, OrderSide, OrderType

logger = logging.getLogger("MM_Agent")

class MarketMakingAgent(StrategyAgent):
    """
    Simple Market Maker.
    Places Buy Limit at Best Bid - Spread and Sell Limit at Best Ask + Spread.
    """
    def __init__(self):
        super().__init__(strategy_id="market_maker_v1", symbols=["SOL/USD"])
        self.spread_target = 0.002 # 0.2%
        self.order_size = 10 # Units
        
    async def on_tick(self, data: MarketData):
        # Real MM needs OrderBook stream (bids/asks), not just last price.
        # MVP: Use last price +- spread
        
        bid_price = data.price * (1 - self.spread_target/2)
        ask_price = data.price * (1 + self.spread_target/2)
        
        # In reality, we must cancel previous orders before placing new ones to avoid inventory bloat
        # signals = [CancelAll(), Order(Buy), Order(Sell)]
        # For MVP log purpose:
        logger.debug(f"Adjusting MM quotes: Bid {bid_price} / Ask {ask_price}")
        
        # We don't spam orders in this MVP to avoid flooding logs, 
        # but here we would emit LIMIT orders
        
    async def run(self):
        while self.running:
            await asyncio.sleep(1)

if __name__ == "__main__":
    agent = MarketMakingAgent()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(agent.start())
