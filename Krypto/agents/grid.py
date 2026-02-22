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
        self.max_capital_allocation = 1000.0  # Limit maximum capital exposed
        self.hard_stop_pct = 0.05  # 5% max drawdown from center

    async def liquidate_all_positions(self):
        logger.warning("Liquidating all open grid positions and cancelling limits due to Hard Stop Loss...")
        # Add actual liquidation logic over broker here

    async def on_tick(self, data: MarketData):
        if self.center_price is None:
            self.center_price = data.price
            self.initialize_grid(data.price)
            return
            
        if data.price <= self.center_price * (1 - self.hard_stop_pct):
            logger.error(f"HARD STOP LOSS: Price ({data.price}) dropped 5% below center ({self.center_price}).")
            await self.liquidate_all_positions()
            self.running = False
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
