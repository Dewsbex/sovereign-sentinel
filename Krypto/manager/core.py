import asyncio
import logging
import os
from shared.broker import MessageBroker
from shared.schemas import TradeSignal, MarketData, AuditLogEntry
import ccxt.async_support as ccxt
from .ratelimit import DecayingTokenBucket
from .normalization import Normalizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ExecutionManager")

class ExecutionManager:
    def __init__(self):
        self.broker = MessageBroker()
        
        # Kraken Tier Intermediate: 20 bursts, decay 0.5 per sec (approx)
        self.rate_limiter = DecayingTokenBucket(capacity=20, decay_rate=0.5)
        self.running = False
        
        # Kraken Exchange Setup
        self.exchange = None
        self.api_key = os.getenv("KRAKEN_API_KEY")
        self.api_secret = os.getenv("KRAKEN_SECRET")
        self.live_mode = os.getenv("KRYPTO_LIVE", "false").lower() == "true"
        
        if not self.api_key or not self.api_secret:
            logger.warning("⚠️  KRAKEN_API_KEY/SECRET not found. Running in DRY-RUN mode.")
        else:
            self.exchange = ccxt.kraken({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
            })

    async def start(self):
        logger.info(f"Starting Execution Manager (LIVE={self.live_mode})...")
        await self.broker.connect()
        self.running = True
        
        # Start the consumer loop
        await self.process_signals()

    async def process_signals(self):
        logger.info("Listening for trade signals...")
        while self.running:
            # Check for Vacation Mode
            lock_relative = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vacation.lock")
            lock_absolute = "/home/ubuntu/Sovereign-Sentinel/vacation.lock"
            
            if os.path.exists(lock_relative) or os.path.exists(lock_absolute):
                logger.warning("🌴 VACATION MODE ACTIVE: Krypto execution paused.")
                await asyncio.sleep(60)
                continue

            try:
                # Consume signal (blocking wait)
                signal = await self.broker.consume_signals()
                logger.info(f"Received signal from {signal.strategy_id}: {signal.side} {signal.symbol}")
                
                # Normalize Data
                normalized_amount = Normalizer.normalize_amount(signal.symbol, signal.amount)
                
                # Check Rate Limit
                if await self.rate_limiter.consume(cost=1):
                    signal.amount = normalized_amount
                    await self.execute_trade(signal)
                else:
                    logger.warning(f"Rate limit hit! Deflecting signal {signal.signal_id}")
                    
            except Exception as e:
                logger.error(f"Error in signal loop: {e}")
                await asyncio.sleep(1)

    async def execute_trade(self, signal: TradeSignal):
        """Execute the trade via CCXT."""
        logger.info(f"⚡ ACTION: {signal.side.upper()} {signal.amount} {signal.symbol} (Reason: {signal.reason})")
        
        if not self.live_mode:
            logger.info("🧪 DRY-RUN: Order skipped (KRYPTO_LIVE=false)")
            await self._log_execution(signal, "dry_run")
            return

        if not self.exchange:
            logger.error("❌ SHUTDOWN: Exchange not initialized!")
            return

        try:
            # 1. Map side and type to CCXT format
            side = signal.side.value # 'buy' or 'sell'
            order_type = 'market' # Defaulting to market for MVP speed
            
            # 2. Execute Order
            # Kraken symbols in CCXT are like 'BTC/USD'
            response = await self.exchange.create_order(
                symbol=signal.symbol,
                type=order_type,
                side=side,
                amount=signal.amount
            )
            
            logger.info(f"✅ SUCCESS: Kraken ID {response['id']}")
            await self._log_execution(signal, "success", response['id'])

        except Exception as e:
            logger.error(f"❌ EXECUTION FAILED: {e}")
            await self._log_execution(signal, "failed", str(e))

    async def _log_execution(self, signal: TradeSignal, status: str, order_id: str = "-"):
        """Log the result to the broker."""
        await self.broker.log_audit(AuditLogEntry(
            component="execution_manager",
            action="order_placed" if status == "success" else f"order_{status}",
            details={
                "signal_id": signal.signal_id,
                "symbol": signal.symbol,
                "amount": signal.amount,
                "order_id": order_id,
                "status": status
            },
            strategy_id=signal.strategy_id
        ))

if __name__ == "__main__":
    manager = ExecutionManager()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(manager.start())
    except KeyboardInterrupt:
        logger.info("Stopping Manager...")

