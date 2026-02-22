import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, time
import zoneinfo
from .base import StrategyAgent
from shared.schemas import TradeSignal, MarketData, OrderSide, OrderType
try:
    from audit_log import AuditLogger
except ImportError:
    # Fallback for standalone testing
    class AuditLogger:
        def __init__(self, name): pass
        def log(self, *args): pass

logger = logging.getLogger("ORB_Agent")

class AugmentedORBAgent(StrategyAgent):
    def __init__(self):
        super().__init__(strategy_id="augmented_orb_v1", symbols=["BTC/USD", "ETH/USD", "SOL/USD"])
        self.audit = AuditLogger("AGT01-KryptoORB")
        self.audit.log("INIT", "System", "ORB Agent Initialized", "INFO")
        self.ny_tz = zoneinfo.ZoneInfo("America/New_York")
        self.orb_duration = 15 # minutes
        
        # Ranges
        self.high_15m = -1.0
        self.low_15m = float('inf')
        self.midpoint = 0.0
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
        # Dynamic Timezone Handling (America/New_York)
        now_ny = datetime.now(self.ny_tz)
        now_time = now_ny.time()
        market_open = time(9, 30)
        market_open_end = time(9, 45) # 9:30 + 15 mins
        
        # VWAP Calculation (Intraday)
        self.tick_count += 1
        self.total_volume += data.volume
        self.cumulative_pv += (data.price * data.volume)
        if self.total_volume > 0:
            self.vwap = self.cumulative_pv / self.total_volume
        
        # Reset Logic for new day
        if now_time < market_open:
            if self.session_active:
                logger.info("New trading session sequence: Resetting ORB ranges.")
            self.session_active = False
            self.high_15m = -1.0
            self.low_15m = float('inf')
            self.total_volume = 0
            self.cumulative_pv = 0
            return

        # 1. IDENTIFICATION: 09:30 - 09:45 NY Time (respecting DST)
        if market_open <= now_time < market_open_end:
            if data.price > self.high_15m: self.high_15m = data.price
            if data.price < self.low_15m: self.low_15m = data.price
            return

        if not self.session_active and self.high_15m > 0:
            self.midpoint = (self.high_15m + self.low_15m) / 2
            logger.info(f"ORB READY: High={self.high_15m}, Low={self.low_15m}, Midpoint={self.midpoint:.2f}, Initial VWAP={self.vwap:.2f}")
            self.session_active = True

        if not self.session_active:
            return

        # 3. FILTERS (SMC / VWAP)
        # LONG: Price > HIGH and Price > VWAP
        if data.price > self.high_15m:
             if data.price > self.vwap:
                 logger.info(f"🔥 BULLISH BREAKOUT: Price {data.price} > High {self.high_15m} AND VWAP {self.vwap:.2f}")
                 await self.send_order(
                     symbol=data.symbol, 
                     side=OrderSide.BUY, 
                     amount=0.01, 
                     reason=f"ORB+VWAP Breakout High",
                     stop_loss=self.midpoint
                 )
                 self.session_active = False # One shot
                 self.audit.log("TRIGGER_BUY", data.symbol, f"Breakout High {self.high_15m} VWAP {self.vwap:.2f}", "SUCCESS")
             else:
                 logger.debug(f"⚠️ Fakeout? Price > High but < VWAP ({self.vwap:.2f})")

        # SHORT: Price < LOW and Price < VWAP
        elif data.price < self.low_15m:
             if data.price < self.vwap:
                 logger.info(f"❄️ BEARISH BREAKOUT: Price {data.price} < Low {self.low_15m} AND VWAP {self.vwap:.2f}")
                 await self.send_order(
                     symbol=data.symbol, 
                     side=OrderSide.SELL, 
                     amount=0.01, 
                     reason=f"ORB+VWAP Breakout Low",
                     stop_loss=self.midpoint
                 )
                 self.session_active = False
                 self.audit.log("TRIGGER_SELL", data.symbol, f"Breakout Low {self.low_15m} VWAP {self.vwap:.2f}", "SUCCESS")
             else:
                 logger.debug(f"⚠️ Fakeout? Price < Low but > VWAP ({self.vwap:.2f})")

    async def run(self):
        logger.info("ORB Agent running... waiting for market open 09:30 AM America/New_York")
        while self.running:
            await asyncio.sleep(60)
            # Periodic health check or cleanup can go here

if __name__ == "__main__":
    agent = AugmentedORBAgent()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(agent.start())
