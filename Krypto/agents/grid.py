import asyncio
import logging
from .base import StrategyAgent
from shared.schemas import TradeSignal, MarketData, OrderSide, OrderType

logger = logging.getLogger("Grid_Agent")

class GeometricGridAgent(StrategyAgent):
    """
    Simple Grid Bot:
    - Defines a center price (e.g. current price at start).
    - Places limits at +1%, +2%... and -1%, -2%...
    """
    def __init__(self):
        super().__init__(strategy_id="geometric_grid_v1", symbols=["BTC/USD"])
        self.center_price = None
        self.grid_levels = []
        self.grid_step = 0.01 # 1%
        self.active_orders = {}

    async def on_tick(self, data: MarketData):
        if self.center_price is None:
            self.center_price = data.price
            self.initialize_grid(data.price)
            return
            
        # Monitor for fills (in real system, we'd get OrderUpdate events)
        # For simulation, we check if price crossed a level
        # ... logic to replenish grid lines ...

    def initialize_grid(self, price):
        logger.info(f"Initializing Grid at {price}")
        # Place 5 buy limits and 5 sell limits
        for i in range(1, 6):
            buy_price = price * (1 - self.grid_step * i)
            sell_price = price * (1 + self.grid_step * i)
            
            # self.send_order uses await, so we need to schedule these or make this async
            # For now just logging the plan
            logger.info(f"Planned Buy Limit: {buy_price}")
            logger.info(f"Planned Sell Limit: {sell_price}")
            
    async def run(self):
         logger.info("Grid Agent initialized.")
         while self.running:
            await asyncio.sleep(10)

if __name__ == "__main__":
    agent = GeometricGridAgent()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(agent.start())
