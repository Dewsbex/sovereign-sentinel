#!/bin/bash
# Sovereign Janitor: Log Archival Script
# Archives logs > 90 days to /home/ubuntu/archive

LOG_DIR="/home/ubuntu/logs"
ARCHIVE_DIR="/home/ubuntu/archive"
TIMESTAMP=$(date +%Y%m%d)

mkdir -p "$ARCHIVE_DIR"

# Find and zip files older than 90 days in logs/
find "$LOG_DIR" -name "*.log" -mtime +90 -exec zip -r "$ARCHIVE_DIR/logs_$TIMESTAMP.zip" {} +
find "$LOG_DIR" -name "*.log" -mtime +90 -delete

# Find and zip files older than 90 days in data/ (Audit logs)
find "/home/ubuntu/Sovereign-Sentinel/data" -name "*.csv" -mtime +90 -exec zip -r "$ARCHIVE_DIR/data_$TIMESTAMP.zip" {} +
find "/home/ubuntu/Sovereign-Sentinel/data" -name "*.csv" -mtime +90 -delete

echo "🧹 [$(date)] Archived old logs to $ARCHIVE_DIR" >> "$LOG_DIR/janitor.log"
