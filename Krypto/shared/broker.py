import redis.asyncio as redis
import json
import logging
import asyncio
import sys
import os
from typing import Callable, Awaitable
from .schemas import TradeSignal, MarketData, AuditLogEntry

logger = logging.getLogger(__name__)

# Dual-write: also log to centralized orchestrator audit trail
_CENTRAL_AVAILABLE = False
try:
    # 1. Try local dev path
    sys.path.append(r"C:\Users\steve\.gemini\antigravity\orchestrator")
    from audit_trail import CentralAuditLogger
    _CENTRAL_AVAILABLE = True
except ImportError:
    # 2. Try relative import (VPS / Production)
    try:
        from shared.audit_trail import CentralAuditLogger
        _CENTRAL_AVAILABLE = True
    except ImportError:
        _CENTRAL_AVAILABLE = False

class MessageBroker:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_url = f"redis://{host}:{port}/{db}"
        self.redis = None
        self.pubsub = None
        # Init central audit logger if available
        self._central = CentralAuditLogger("krypto") if _CENTRAL_AVAILABLE else None

    async def connect(self):
        self.redis = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
        self.pubsub = self.redis.pubsub()
        logger.info(f"Connected to Redis at {self.redis_url}")

    async def publish_signal(self, signal: TradeSignal):
        """Publish a trade signal to the execution queue."""
        await self.redis.rpush("orders.new", signal.model_dump_json())
        logger.debug(f"Published signal: {signal.signal_id}")

    async def publish_market_data(self, data: MarketData):
        """Publish market data to a specific topic."""
        channel = f"market_data.{data.symbol}"
        await self.redis.publish(channel, data.model_dump_json())

    async def log_audit(self, entry: AuditLogEntry):
        """Log an audit entry to the central log stream."""
        # 1. Redis Stream (for Krypto internal durability)
        await self.redis.xadd("system.audit_log", entry.model_dump())
        
        # 2. Central SQLite (for orchestrator forensics)
        if self._central:
            try:
                # Use to_thread to avoid blocking the async event loop with SQLite I/O
                await asyncio.to_thread(
                    self._central.log,
                    action=entry.action,
                    target=entry.component,
                    details=json.dumps(entry.details),
                    severity=entry.level
                )
            except Exception as e:
                logger.warning(f"Failed to write to central audit log: {e}")

    async def subscribe_to_market_data(self, symbols: list[str], callback: Callable[[MarketData], Awaitable[None]]):
        """
        Subscribe to market data channels and trigger a callback.
        This blocks the loop, so run it as a task.
        """
        channels = [f"market_data.{s}" for s in symbols]
        await self.pubsub.subscribe(*channels)
        
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = MarketData.model_validate_json(message['data'])
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error processing market data: {e}")

    async def consume_signals(self) -> TradeSignal:
        """
        Blocking pop from the order queue.
        Returns a TradeSignal when available.
        """
        # blpop returns (key, value) tuple
        _, data = await self.redis.blpop("orders.new")
        return TradeSignal.model_validate_json(data)
