import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, time
from .base import StrategyAgent
from shared.schemas import TradeSignal, MarketData, OrderSide, OrderType

logger = logging.getLogger("ORB_Agent")

class AugmentedORBAgent(StrategyAgent):
    def __init__(self):
        super().__init__(strategy_id="augmented_orb_v1", symbols=["BTC/USD", "ETH/USD"])
        self.market_open = time(13, 30) # 13:30 UTC
        self.orb_duration = 15 # minutes
        
        # Ranges
        self.high_15m = -1.0
        self.low_15m = float('inf')
        self.session_active = False
        
        # SMC / Technicals
        self.tick_count = 0
        self.total_volume = 0.0
        self.cumulative_pv = 0.0 # Price * Volume for VWAP
        self.vwap = 0.0

    async def on_tick(self, data: MarketData):
        """
        Ingest ticks and calculate VWAP + ORB Breakouts.
        """
        now = datetime.utcnow().time()
        
        # VWAP Calculation (Intraday)
        self.tick_count += 1
        self.total_volume += data.volume
        self.cumulative_pv += (data.price * data.volume)
        if self.total_volume > 0:
            self.vwap = self.cumulative_pv / self.total_volume
        
        # Reset Logic for new day
        if now < self.market_open:
            if self.session_active:
                logger.info("New trading session sequence: Resetting ORB ranges.")
            self.session_active = False
            self.high_15m = -1.0
            self.low_15m = float('inf')
            self.total_volume = 0
            self.cumulative_pv = 0
            return

        # 1. IDENTIFICATION: 13:30 - 13:45
        if self.market_open <= now < time(13, 30 + self.orb_duration):
            if data.price > self.high_15m: self.high_15m = data.price
            if data.price < self.low_15m: self.low_15m = data.price
            return

        # 2. MONITORING / EXECUTION: After 13:45
        if not self.session_active and self.high_15m > 0:
            logger.info(f"ORB READY: High={self.high_15m}, Low={self.low_15m}, Initial VWAP={self.vwap:.2f}")
            self.session_active = True

        if not self.session_active:
            return

        # 3. FILTERS (SMC / VWAP)
        # LONG: Price > HIGH and Price > VWAP
        if data.price > self.high_15m:
             if data.price > self.vwap:
                 logger.info(f"🔥 BULLISH BREAKOUT: Price {data.price} > High {self.high_15m} AND VWAP {self.vwap:.2f}")
                 await self.send_order(data.symbol, OrderSide.BUY, 0.01, f"ORB+VWAP Breakout High")
                 self.session_active = False # One shot
             else:
                 logger.debug(f"⚠️ Fakeout? Price > High but < VWAP ({self.vwap:.2f})")

        # SHORT: Price < LOW and Price < VWAP
        elif data.price < self.low_15m:
             if data.price < self.vwap:
                 logger.info(f"❄️ BEARISH BREAKOUT: Price {data.price} < Low {self.low_15m} AND VWAP {self.vwap:.2f}")
                 await self.send_order(data.symbol, OrderSide.SELL, 0.01, f"ORB+VWAP Breakout Low")
                 self.session_active = False
             else:
                 logger.debug(f"⚠️ Fakeout? Price < Low but > VWAP ({self.vwap:.2f})")

    async def run(self):
        logger.info("ORB Agent running... waiting for market open 13:30 UTC")
        while self.running:
            await asyncio.sleep(60)
            # Periodic health check or cleanup can go here

if __name__ == "__main__":
    agent = AugmentedORBAgent()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(agent.start())
