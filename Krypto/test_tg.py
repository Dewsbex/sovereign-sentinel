from telegram_bot import SovereignAlerts
print('Testing...')
try:
    SovereignAlerts().send_message(' SYSTEM TEST: Manual Connectivity Check')
    print('Message Sent.')
except Exception as e:
    print(f'Error: {e}')
