# Rclone Cheatsheet for Google Drive

## Configuration

```bash
# List configured remotes
rclone listremotes

# Configure a new Google Drive remote
rclone config

# Reconnect/refresh authentication
rclone config reconnect gdrive:

# Show remote configuration
rclone config show gdrive:
```

## Basic Operations

### Directory Operations
```bash
# List directories
rclone lsd gdrive:

# List files with sizes
rclone ls gdrive:path/

# List files only (names)
rclone lsf gdrive:path/

# Tree view
rclone tree gdrive:path/

# Create directory
rclone mkdir gdrive:newdir
```

### Copy Operations
```bash
# Copy file
rclone copy /local/file.txt gdrive:remote/path/

# Copy directory (recursive)
rclone copy /local/dir gdrive:remote/path/ -P

# Sync (mirror local → remote)
rclone sync /local gdrive:remote/ -P

# Move (copy + delete source)
rclone move /local gdrive:remote/ -P
```

## Advanced Options

### Filtering
```bash
# Include/exclude patterns
rclone copy /src gdrive:dst/ --include "*.pdf" --exclude "*.tmp"
rclone copy /src gdrive:dst/ --exclude "temp/**" --exclude "*.log"

# Size filters
rclone copy /src gdrive:dst/ --min-size 1M --max-size 100M

# Time filters
rclone copy /src gdrive:dst/ --max-age 7d    # last 7 days
rclone copy /src gdrive:dst/ --min-age 1h    # older than 1 hour
```

### Performance & Bandwidth
```bash
# Limit bandwidth
rclone copy /src gdrive:dst/ --bwlimit 2M    # 2 MB/s
rclone copy /src gdrive:dst/ --bwlimit 08:00,1M 20:00,off  # schedule

# Transfers and retries
rclone copy /src gdrive:dst/ --transfers 4   # parallel transfers
rclone copy /src gdrive:dst/ --retries 3     # retry on failure
rclone copy /src gdrive:dst/ --low-level-retries 10
```

### Verification & Safety
```bash
# Dry run (test)
rclone copy /src gdrive:dst/ --dry-run

# Checksum verification
rclone copy /src gdrive:dst/ --checksum

# Compare source and destination
rclone check /src gdrive:dst/

# Size only check
rclone check /src gdrive:dst/ --size-only
```

## Monitoring & Logging

```bash
# Show progress
rclone copy /src gdrive:dst/ -P

# Verbose output
rclone copy /src gdrive:dst/ -v

# Log to file
rclone copy /src gdrive:dst/ --log-file=rclone.log --log-level INFO

# Stats
rclone copy /src gdrive:dst/ --stats 10s     # update every 10s
```

## Troubleshooting

```bash
# Check version
rclone version

# Debug HTTP traffic
rclone copy /src gdrive:dst/ -vv --dump headers

# List available commands
rclone help

# Get help for specific command
rclone help copy
rclone help flags
```

## Google Drive Specific

```bash
# List Google Drive team drives
rclone lsd gdrive: --drive-shared-with-me

# Use server-side copies (fast)
rclone copy gdrive:src gdrive:dst/ --drive-server-side-across-configs

# Export Google Docs as PDF/Office
rclone copy gdrive:document.gdoc /local/ --drive-export-formats pdf,docx

# Avoid rate limits
rclone copy /src gdrive:dst/ --drive-chunk-size 64M --tpslimit 10
```

## Common Use Cases

### Backup with timestamp
```bash
BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
rclone copy /important gdrive:Backups/$BACKUP_NAME/ -P --checksum
```

### Sync with exclusion
```bash
rclone sync /projects gdrive:Projects/ \
  --exclude "node_modules/" \
  --exclude ".git/" \
  --exclude "*.pyc" \
  -P
```

### Mirror with deletion
```bash
rclone sync /website gdrive:WebsiteMirror/ --delete-during -P
```

### Incremental update
```bash
# Only files modified in last 24 hours
rclone copy /data gdrive:Data/ --max-age 24h -P
```