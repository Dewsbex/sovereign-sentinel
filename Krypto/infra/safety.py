import asyncio
import logging
from shared.broker import MessageBroker
from shared.schemas import TradeSignal, MarketData, AuditLogEntry

logger = logging.getLogger("SafetyMonitor")

class SafetyMonitor:
    def __init__(self):
        self.broker = MessageBroker()
        self.running = False
        self.total_loss_24h = 0.0
        self.max_loss_threshold = 1000.0 # Max daily loss in USD
        self.active_agents_count = 0

    async def start(self):
        logger.info("Safety Monitor Starting...")
        await self.broker.connect()
        self.running = True
        
        # Subscribe to audit logs to track P/L
        # Note: Redis Streams reading is more complex, here we assume a simpler pub/sub for critical alerts
        # or polling the stream.
        await self.monitor_loop()

    async def monitor_loop(self):
        while self.running:
            # Check for critical system health
            # 1. Redis connectivity
            if not await self.check_redis():
                await self.trigger_kill_switch("Redis Disconnected")
            
            # 2. Daily Loss Limit (Mocked logic)
            if self.total_loss_24h > self.max_loss_threshold:
                 await self.trigger_kill_switch(f"Daily Loss Limit Exceeded: {self.total_loss_24h}")

            await asyncio.sleep(5)

    async def check_redis(self) -> bool:
        try:
            return await self.broker.redis.ping()
        except:
            return False

    async def trigger_kill_switch(self, reason: str):
        logger.critical(f"🚨 KILL SWITCH TRIGGERED: {reason}")
        # Publish a high-priority 'kill' message that all agents subscribe to
        await self.broker.redis.publish("system.control", "KILL")
        
        # Also could forcibly cancel all orders via Manager
        await self.broker.log_audit({
            "action": "KILL_SWITCH",
            "component": "SafetyMonitor",
            "details": {"reason": reason},
            "level": "CRITICAL"
        })

if __name__ == "__main__":
     monitor = SafetyMonitor()
     loop = asyncio.get_event_loop()
     loop.run_until_complete(monitor.start())
