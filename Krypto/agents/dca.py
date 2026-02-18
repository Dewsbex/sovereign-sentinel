import asyncio
import logging
from enum import Enum
from .base import StrategyAgent
from shared.schemas import TradeSignal, MarketData, OrderSide, OrderType

logger = logging.getLogger("DCA_Agent")

class DCAMode(str, Enum):
    GEOMETRIC = "geometric"   # Linear spacing, Linear sizing
    MARTINGALE = "martingale" # Linear spacing, Exponential sizing

class DCAAgent(StrategyAgent):
    def __init__(self, mode: DCAMode = DCAMode.GEOMETRIC):
        super().__init__(strategy_id=f"dca_{mode.value}_v1", symbols=["BTC/USD"])
        self.mode = mode
        self.entry_price = None
        self.base_order_size = 0.001
        self.safety_orders_count = 0
        self.max_safety_orders = 10
        self.price_deviation = 0.02 # 2% drop triggers safety order

    async def on_tick(self, data: MarketData):
        if self.entry_price is None:
            # First buy
            self.entry_price = data.price
            await self.send_order(data.symbol, OrderSide.BUY, self.base_order_size, "DCA Initial Entry")
            logger.info(f"DCA Started at {self.entry_price}")
            return

        # Check for safety order trigger
        current_drop = (self.entry_price - data.price) / self.entry_price
        
        # Target drop for next safety order: (count + 1) * deviation
        target_drop = (self.safety_orders_count + 1) * self.price_deviation
        
        if current_drop >= target_drop and self.safety_orders_count < self.max_safety_orders:
            # Calculate size
            if self.mode == DCAMode.MARTINGALE:
                # Double down
                size = self.base_order_size * (2 ** (self.safety_orders_count + 1))
            else:
                # Fixed size
                size = self.base_order_size
                
            await self.send_order(data.symbol, OrderSide.BUY, size, f"DCA Safety Order #{self.safety_orders_count + 1}")
            self.safety_orders_count += 1
            logger.info(f"DCA Safety Order Triggered. Count: {self.safety_orders_count}")

    async def run(self):
        while self.running:
            await asyncio.sleep(1)

if __name__ == "__main__":
    agent = DCAAgent(mode=DCAMode.MARTINGALE)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(agent.start())
