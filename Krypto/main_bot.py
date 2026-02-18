import asyncio
import logging
import os
import signal
import sys
from manager.core import ExecutionManager
from agents.orb import AugmentedORBAgent
from agents.sentiment import CrossProjectSentimentAgent

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/krypto_unified.log")
    ]
)
logger = logging.getLogger("KryptoMain")

class KryptoEngine:
    def __init__(self):
        self.manager = ExecutionManager()
        self.agents = [
            AugmentedORBAgent(),
            CrossProjectSentimentAgent()
        ]
        self.tasks = []
        self.running = False

    async def start(self):
        logger.info("🚀 INITIALIZING KRYPTO UNIFIED ENGINE")
        
        # 1. Start Execution Manager
        self.tasks.append(asyncio.create_task(self.manager.start()))
        
        # Give the manager a moment to connect to Redis
        await asyncio.sleep(2)
        
        # 2. Start Agents
        for agent in self.agents:
            self.tasks.append(asyncio.create_task(agent.start()))
            
        self.running = True
        logger.info(f"✅ Engine Online | Agents: {len(self.agents)} | Mode: {'LIVE' if self.manager.live_mode else 'DRY-RUN'}")
        
        try:
            # Keep the main loop running
            while self.running:
                await asyncio.sleep(60)
                # Periodic health check of tasks can go here
        except asyncio.CancelledError:
            logger.info("Engine shutdown signal received.")
        except Exception as e:
            logger.error(f"Critical Engine Failure: {e}")
        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        logger.info("🛑 SHUTTING DOWN KRYPTO ENGINE")
        for agent in self.agents:
            await agent.stop()
        # manager stop logic if any
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        logger.info("👋 Shutdown Complete")

def handle_sigterm(*args):
    raise SystemExit

if __name__ == "__main__":
    # Ensure logs dir exists
    os.makedirs("logs", exist_ok=True)
    
    engine = KryptoEngine()
    
    # Handle OS signals for clean exit
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(engine.stop()))

    try:
        loop.run_until_complete(engine.start())
    except KeyboardInterrupt:
        pass
    except SystemExit:
        pass
