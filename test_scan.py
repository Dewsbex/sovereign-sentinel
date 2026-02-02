import logging
import sys
from main_bot import Strategy_ORB

# Mock logger for console
logging.basicConfig(level=logging.INFO)

def test_scan():
    print("🚀 Running Diagnostics: ORB Scanner Test")
    bot = Strategy_ORB()
    
    # Force simulation mode for scanning
    print(f"Watchlist: {bot.watchlist}")
    
    # 1. Start Scan
    bot.scan_candidates(bot.watchlist)
    
    print(f"\nResults of scan:")
    print(f"Status: {bot.status}")
    print(f"Candidates Qualified: {bot.watchlist}")
    
    # 2. Try Observation (if any candidates)
    if bot.watchlist:
        print("\n🔭 Testing Observation Module...")
        bot.monitor_observation_window()
        print(f"Final Status: {bot.status}")
        print(f"Locked Levels: {bot.orb_levels.keys()}")
        for t, levels in bot.orb_levels.items():
            print(f"   🎯 {t}: High {levels['high']:.2f} | Low {levels['low']:.2f} | RVOL {levels['rvol']:.2f}")

if __name__ == "__main__":
    test_scan()
