import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from shared.broker import MessageBroker
from shared.schemas import TradeSignal, MarketData, OrderSide, OrderType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StrategyAgent")

class StrategyAgent(ABC):
    def __init__(self, strategy_id: str, symbols: list[str]):
        self.strategy_id = strategy_id
        self.symbols = symbols
        self.broker = MessageBroker()
        self.running = False
        self.logger = logging.getLogger(f"Agent.{strategy_id}")

    async def start(self):
        """Standard startup sequence."""
        self.logger.info(f"Starting agent: {self.strategy_id}")
        await self.broker.connect()
        self.running = True
        
        # Subscribe to market data
        # We start a background task to listen for market updates
        asyncio.create_task(self.broker.subscribe_to_market_data(self.symbols, self.on_tick))
        
        # Run strategy main loop (if needed by subclass)
        await self.run()

    async def run(self):
        """Optional main loop for strategy logic (e.g. polling)."""
        while self.running:
            await asyncio.sleep(1)

    @abstractmethod
    async def on_tick(self, data: MarketData):
        """
        Callback triggered when new market data arrives.
        Must be implemented by subclasses.
        """
        pass

    async def send_order(self, symbol: str, side: OrderSide, amount: float, reason: str, 
                         order_type: OrderType = OrderType.MARKET, price: float = None):
        """
        Helper to construct and publish a TradeSignal.
        """
        signal = TradeSignal(
            strategy_id=self.strategy_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            reason=reason
        )
        self.logger.info(f"Signal generated: {side} {symbol}")
        await self.broker.publish_signal(signal)

    async def stop(self):
        self.running = False
        self.logger.info("Stopping agent...")
