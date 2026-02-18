import os
import sys
from datetime import datetime

# Setup paths
sys.path.append(os.getcwd())

from strategic_moat import MorningBrief
from audit_log import AuditLogger

def force_run():
    print("🚀 Forcing Morning Brief Generation...")
    logger = AuditLogger("Manual-Trigger")
    
    try:
        brief = MorningBrief()
        brief.generate_brief()
        
        # Update lock file to prevent double run by bot
        today_str = datetime.utcnow().strftime('%Y-%m-%d')
        with open('data/open_brief.lock', 'w') as f:
            f.write(today_str)
            
        print("✅ Morning Brief Complete. Targets updated.")
        logger.log("MANUAL_BRIEF", "User", "Forced generation of Morning Brief", "SUCCESS")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.log("MANUAL_BRIEF_ERROR", "User", str(e), "ERROR")

if __name__ == "__main__":
    force_run()
