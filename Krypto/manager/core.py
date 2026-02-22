import asyncio
import logging
import os
import sys

# Add root to sys.path for credentials_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from credentials_manager import get_secret

from shared.broker import MessageBroker
from shared.schemas import TradeSignal, MarketData, AuditLogEntry
import ccxt
from .ratelimit import DecayingTokenBucket
from .normalization import Normalizer
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ExecutionManager")

class ExecutionManager:
    def __init__(self):
        self.broker = MessageBroker()
        self.rate_limiter = DecayingTokenBucket(capacity=20, decay_rate=0.5)
        self.running = False
        self.exchange = None
        self.api_key = get_secret("KRAKEN_API_KEY")
        self.api_secret = get_secret("KRAKEN_SECRET")
        self.live_mode = get_secret("KRYPTO_LIVE").lower() == "true" if get_secret("KRYPTO_LIVE") else False
        
        if not self.api_key or not self.api_secret:
            logger.warning("KRAKEN_API_KEY/SECRET not found. Running in DRY-RUN mode.")
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
        await self.process_signals()

    async def process_signals(self):
        logger.info("Listening for trade signals...")
        while self.running:
            # Check for Vacation Mode
            lock_relative = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vacation.lock")
            if os.path.exists(lock_relative):
                logger.warning("VACATION MODE ACTIVE: Krypto execution paused.")
                await asyncio.sleep(60)
                continue
            try:
                signal = await self.broker.consume_signals()
                logger.info(f"Received signal from {signal.strategy_id}: {signal.side} {signal.symbol}")
                normalized_amount = Normalizer.normalize_amount(signal.symbol, signal.amount)
                if await self.rate_limiter.consume(cost=1):
                    # Hardened Spread Audit Check (0.05% Threshold)
                    if self.check_spread_audit(signal.symbol):
                         signal.amount = normalized_amount
                         await self.execute_trade(signal)
                    else:
                         logger.warning(f"SPREAD ABORT: Excessive spread for {signal.symbol}. Trade skipped.")
                         await self._log_execution(signal, "aborted_high_spread")
                else:
                    logger.warning(f"Rate limit hit! Deflecting signal {signal.signal_id}")
            except Exception as e:
                logger.error(f"Error in signal loop: {e}")
                await asyncio.sleep(1)

    async def execute_trade(self, signal: TradeSignal):
        logger.info(f"ACTION: {signal.side.upper()} {signal.amount} {signal.symbol}")
        if not self.live_mode:
            logger.info("DRY-RUN: Order skipped")
            await self._log_execution(signal, "dry_run")
            return
        if not self.exchange:
            logger.error("Exchange not initialized!")
            return
        try:
            side = signal.side.value
            # Synchronous call since aiohttp is broken in this environment
            response = self.exchange.create_order(
                symbol=signal.symbol,
                type='market',
                side=side,
                amount=signal.amount
            )
            logger.info(f"SUCCESS: Kraken ID {response['id']}")
            
            # Implementation of Midpoint Stop Loss (Structural Stop)
            if signal.stop_loss:
                await self.submit_stop_loss(signal, response['id'])
                
            await self._log_execution(signal, "success", response['id'])
        except Exception as e:
            logger.error(f"EXECUTION FAILED: {e}")
            await self._log_execution(signal, "failed", str(e))

    async def _log_execution(self, signal: TradeSignal, status: str, order_id: str = "-"):
        await self.broker.log_audit(AuditLogEntry(
            component="execution_manager",
            action="order_placed" if status == "success" else f"order_{status}",
            details={"signal_id": signal.signal_id, "symbol": signal.symbol, "status": status, "order_id": order_id},
            strategy_id=signal.strategy_id
        ))

    def check_spread_audit(self, symbol: str) -> bool:
        """
        Queries Kraken Depth and verifies if spread < 0.05%.
        """
        try:
            order_book = self.exchange.fetch_order_book(symbol)
            bid = order_book['bids'][0][0] if order_book['bids'] else 0
            ask = order_book['asks'][0][0] if order_book['asks'] else 0
            if bid == 0: return False
            
            spread_pct = (ask - bid) / bid
            logger.info(f"SPREAD AUDIT for {symbol}: {spread_pct:.5f} (Limit: 0.0005)")
            return spread_pct <= 0.0005
        except Exception as e:
            logger.error(f"Spread audit failed: {e}")
            return False

    async def submit_stop_loss(self, signal: TradeSignal, entry_order_id: str):
        """
        Submits a conditional stop loss order at the specified price.
        """
        try:
            # Kraken Spot SL requires side opposite to entry
            sl_side = 'sell' if signal.side == OrderSide.BUY else 'buy'
            logger.info(f"PLACING STOP LOSS: {sl_side.upper()} {signal.amount} {signal.symbol} @ {signal.stop_loss}")
            
            # Using stop-loss-limit for compliance with "Ironclad" spec
            # Price = Trigger, Price2 = Limit (slightly below for sells to ensure fill)
            # For simplicity in this spot-only retail env, we use market stop-loss
            response = self.exchange.create_order(
                symbol=signal.symbol,
                type='stop-loss',
                side=sl_side,
                amount=signal.amount,
                params={'stopPrice': signal.stop_loss}
            )
            logger.info(f"STOP LOSS ACTIVE: ID {response['id']}")
        except Exception as e:
            logger.error(f"Failed to submit stop loss: {e}")

if __name__ == "__main__":
    manager = ExecutionManager()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(manager.start())
    except KeyboardInterrupt:
        pass
