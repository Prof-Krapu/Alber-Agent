#!/bin/bash
# Sync project directory to Google Drive with intelligent exclusions
# Usage: ./sync-project.sh <project_path> <remote_path> [--dry-run]

set -e

PROJECT_PATH="$1"
REMOTE_PATH="$2"
shift 2

# Default exclusions (common development artifacts)
EXCLUDE="--exclude *.pyc --exclude __pycache__/ --exclude node_modules/ --exclude .git/ --exclude .DS_Store --exclude *.tmp --exclude *.log --exclude .env"

# Default options
OPTS="--progress --verbose --retries 2 $EXCLUDE"

# Add dry-run if specified
for arg in "$@"; do
    if [ "$arg" = "--dry-run" ]; then
        OPTS="$OPTS --dry-run"
    else
        OPTS="$OPTS $arg"
    fi
done

# Validate inputs
if [ -z "$PROJECT_PATH" ] || [ -z "$REMOTE_PATH" ]; then
    echo "Usage: $0 <project_path> <remote_path> [--dry-run] [additional_rclone_options]"
    echo "Example: $0 /home/user/projects/myapp gdrive:Projects/myapp --dry-run"
    exit 1
fi

if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project path '$PROJECT_PATH' is not a directory"
    exit 1
fi

echo "Syncing project: $PROJECT_PATH → $REMOTE_PATH"
echo "Options: $OPTS"

# Execute rclone sync
rclone sync "$PROJECT_PATH" "$REMOTE_PATH" $OPTS

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    if [[ "$OPTS" == *"--dry-run"* ]]; then
        echo "Dry run completed - no changes made"
    else
        echo "Project sync completed successfully"
    fi
else
    echo "Sync failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE