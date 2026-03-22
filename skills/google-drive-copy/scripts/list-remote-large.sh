#!/bin/bash
# List large files on Google Drive remote
# Usage: ./list-remote-large.sh <remote_path> [min_size_MB]

set -e

REMOTE_PATH="$1"
MIN_SIZE="${2:-10}"  # Default 10 MB

if [ -z "$REMOTE_PATH" ]; then
    echo "Usage: $0 <remote_path> [min_size_MB]"
    echo "Example: $0 gdrive:Backup 50"
    exit 1
fi

# Convert MB to bytes
MIN_BYTES=$((MIN_SIZE * 1024 * 1024))

echo "Searching for files larger than ${MIN_SIZE}MB in $REMOTE_PATH"
echo "=========================================================="

# Use rclone lsf with size and sort by size descending
rclone lsf "$REMOTE_PATH" --files-only --format "sp" --separator "|" --csv 2>/dev/null | \
    while IFS='|' read -r size path; do
        if [ -n "$size" ] && [ "$size" -gt "$MIN_BYTES" ]; then
            size_mb=$(echo "scale=2; $size / 1024 / 1024" | bc)
            printf "%8.2f MB  %s\n" "$size_mb" "$path"
        fi
    done | sort -rn

# Alternative method using rclone ls and awk
echo ""
echo "Alternative listing (simpler):"
echo "------------------------------"
rclone ls "$REMOTE_PATH" | awk -v min=$MIN_BYTES '$1 > min {size_mb=$1/1024/1024; printf "%8.2f MB  %s\n", size_mb, substr($0, index($0,$2))}' | sort -rn