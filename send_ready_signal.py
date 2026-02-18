from telegram_bot import SovereignAlerts

def send_ready_signal():
    alerts = SovereignAlerts()
    msg = (
        "⚔️ **SYSTEM BATTLE READY** ⚔️\n\n"
        "**Status:** NEON SENTRY (v2.0.1)\n"
        "**Modules:**\n"
        "✅ **Iron Seed Protocol:** Active (Limit: £1,000)\n"
        "✅ **Sector Census:** Active (Lab Filtered)\n"
        "✅ **Master List Sync:** Scheduled (08:30 UTC)\n"
        "✅ **Gemini Brain:** 1.5 Flash (Calibrated)\n\n"
        "The Sovereign Dashboard is LIVE and PROTECTED.\n"
        "Monitoring for US Session Open (14:30 UTC)."
    )
    alerts.send_message(msg)
    print("✅ Battle Ready Signal Sent.")

if __name__ == "__main__":
    send_ready_signal()
