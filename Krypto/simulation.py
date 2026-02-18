import asyncio
import logging
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Simulation")

# --- DEPENDENCY HANDLING ---
try:
    from shared.schemas import TradeSignal, MarketData, OrderSide, OrderType
    from manager.core import ExecutionManager
    from agents.orb import AugmentedORBAgent
    logger.info("Using Project Dependencies.")
except ImportError:
    logger.warning("Project dependencies not found. Using Mock Classes for Simulation Demo.")
    
    # Mock Enums
    class OrderSide:
        BUY = "buy"
        SELL = "sell"
    
    class OrderType:
        MARKET = "market"
        LIMIT = "limit"

    # Mock Data Models (using dataclasses instead of Pydantic)
    @dataclass
    class TradeSignal:
        strategy_id: str
        symbol: str
        side: str
        amount: float
        reason: str
        order_type: str = OrderType.MARKET
        price: Optional[float] = None
        signal_id: str = "mock_sig_1"
        
        def model_dump(self):
            return self.__dict__

    @dataclass
    class MarketData:
        symbol: str
        price: float
        volume: float
        timestamp: datetime = datetime.utcnow()
        
        def model_dump_json(self):
            return str(self.__dict__)

    # Mock Components
    class MockRateLimiter:
        fill_rate = 100
        async def consume(self, strategies_priority=1): return True
        
    class ExecutionManager:
        def __init__(self):
            self.broker = None
            self.rate_limiter = MockRateLimiter()
            self.running = False
        async def start(self):
            self.running = True
            await self.process_signals()
        async def execute_trade(self, signal):
            logger.info(f"⚡ EXECUTING: {signal.side} {signal.amount} {signal.symbol} for {signal.strategy_id}")
        async def process_signals(self):
            while self.running:
                signal = await self.broker.consume_signals()
                await self.execute_trade(signal)

    class AugmentedORBAgent:
        def __init__(self):
            self.broker = None
            self.running = False
            self.market_open = (13, 30)
            self.high_15m = 0
            self.session_active = False
        async def start(self): self.running = True
        async def send_order(self, symbol, side, amount, reason):
            sig = TradeSignal(strategy_id="orb_mock", symbol=symbol, side=side, amount=amount, reason=reason)
            await self.broker.publish_signal(sig)

# --- MOCKS ---
class MockBroker:
    def __init__(self):
        self.signal_queue = asyncio.Queue()
        self.market_queues = []

    async def connect(self):
        logger.info("[MockBroker] Connected (In-Memory)")

    async def publish_signal(self, signal):
        await self.signal_queue.put(signal)

    async def consume_signals(self):
        return await self.signal_queue.get()

    async def log_audit(self, entry):
        logger.info(f"[Audit Log] {entry}")

    async def subscribe_to_market_data(self, symbols, callback):
        self.market_queues.append(callback)

    async def publish_market_data(self, data):
        # In a real scenario, this would distribute to specific channels
        # For simulation, we just call the registered callbacks (if they accept the data)
        # But our simple agents might expect a Pydantic model. 
        # If we are in Mock mode, `MarketData` is a dataclass.
        pass

# --- SIMULATION ---
async def run_simulation():
    mock_broker = MockBroker()
    
    manager = ExecutionManager()
    manager.broker = mock_broker
    
    agent = AugmentedORBAgent()
    agent.broker = mock_broker
    
    # Start Components
    asyncio.create_task(manager.start())
    asyncio.create_task(agent.start()) # In full mode, this would listen to ticks
    
    logger.info("--- Starting Simulation ---")
    
    # Simulate ORB Workflow manually to bypass complex Tick logic in the Mock
    logger.info("Market Open! Tracking Range...")
    await asyncio.sleep(0.5)
    
    logger.info("High Established at 50,500")
    agent.high_15m = 50500
    agent.session_active = True
    
    logger.info("Price breaks 50,600! Triggering Signal...")
    # Manually trigger signal for the mock logic
    await agent.send_order("BTC/USD", OrderSide.BUY, 1.0, "Simulation Breakout")
    
    # Allow time for manager to process
    await asyncio.sleep(1)
    
    logger.info("--- Simulation Complete ---")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        pass
