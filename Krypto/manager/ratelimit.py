import time
import asyncio
import math
from typing import Optional

class DecayingTokenBucket:
    """
    Models Kraken's Rate Limit:
    - User has a 'Ledger' of points (Counter).
    - Max counter value (Capacity).
    - Counter decays (refills) over time.
    - Each request adds points to the counter.
    - If counter > capacity, request is rejected.
    """
    def __init__(self, capacity: int = 20, decay_rate: float = 0.5):
        """
        :param capacity: Max points allowed before lockout (e.g. 20).
        :param decay_rate: Points removed per second (e.g. 0.5 points/sec).
        """
        self.capacity = float(capacity)
        self.decay_rate = float(decay_rate)
        self.counter = 0.0
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self, cost: int = 1) -> bool:
        """
        Attempt to consume 'cost' points.
        Returns True if successful (under capacity), False if rate limited.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now
            
            # Apply Decay (Refill)
            # Counter decreases by decay_rate * elapsed
            self.counter = max(0.0, self.counter - (elapsed * self.decay_rate))
            
            # Check if we have room
            if self.counter + cost <= self.capacity:
                self.counter += cost
                return True
            else:
                return False

    async def wait_for_token(self, cost: int = 1):
        """
        Blocks until enough decay has happened to allow 'cost'.
        """
        while True:
            if await self.consume(cost):
                return
            
            # Calculate wait time
            # We need to decay enough to fit 'cost'
            # current_counter - (wait * decay) + cost <= capacity
            # wait >= (current_counter + cost - capacity) / decay
            async with self._lock: # Peek at counter
                needed = (self.counter + cost - self.capacity)
            
            if needed > 0:
                 wait_time = needed / self.decay_rate
                 await asyncio.sleep(min(wait_time, 0.1)) # Sleep but check frequently
            else:
                 await asyncio.sleep(0.1)

