#!/bin/bash
# Incremental backup to Google Drive with logging
# Usage: ./backup-to-gdrive.sh <local_path> <remote_path> [options]

set -e

LOCAL_PATH="$1"
REMOTE_PATH="$2"
shift 2

# Default options
OPTS="--progress --verbose --retries 3 --checksum --max-age 24h"

# Override with user options if provided
if [ $# -gt 0 ]; then
    OPTS="$*"
fi

# Validate inputs
if [ -z "$LOCAL_PATH" ] || [ -z "$REMOTE_PATH" ]; then
    echo "Usage: $0 <local_path> <remote_path> [rclone_options]"
    echo "Example: $0 /home/user/Documents gdrive:Backup/Documents --dry-run"
    exit 1
fi

if [ ! -e "$LOCAL_PATH" ]; then
    echo "Error: Local path '$LOCAL_PATH' does not exist"
    exit 1
fi

# Create log directory
LOG_DIR="$HOME/.local/log/rclone"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/backup-$(date +%Y%m%d-%H%M%S).log"

echo "Starting backup: $LOCAL_PATH → $REMOTE_PATH"
echo "Options: $OPTS"
echo "Log: $LOG_FILE"

# Execute rclone copy
rclone copy "$LOCAL_PATH" "$REMOTE_PATH" $OPTS 2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo "Backup completed successfully"
else
    echo "Backup failed with exit code $EXIT_CODE"
    echo "Check log: $LOG_FILE"
fi

exit $EXIT_CODE