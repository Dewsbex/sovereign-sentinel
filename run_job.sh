#!/bin/bash
# Universal Job Wrapper with Failure Notification
# Usage: ./run_job.sh <job_name> <command...>

JOB_NAME="$1"
shift
LOG_FILE="/home/ubuntu/logs/${JOB_NAME}.log"
CMD="$@"

# Ensure log dir exists
mkdir -p /home/ubuntu/logs

echo "--- START: $(date) ---" >> "$LOG_FILE"
echo "Executing: $CMD" >> "$LOG_FILE"

# Execute
"$@" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "--- END: $(date) (Exit: $EXIT_CODE) ---" >> "$LOG_FILE"

# Notification on Failure
if [ $EXIT_CODE -ne 0 ]; then
    echo "⚠️ Job Failed. Sending alert..." >> "$LOG_FILE"
    /usr/bin/python3 /home/ubuntu/Sovereign-Sentinel/telegram_bot.py --message "⚠️ **JOB FAILURE**
    Job: \`$JOB_NAME\`
    Exit Code: \`$EXIT_CODE\`
    Check logs: \`/home/ubuntu/logs/${JOB_NAME}.log\`" >> "$LOG_FILE" 2>&1
fi

exit $EXIT_CODE
