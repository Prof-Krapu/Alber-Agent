# Google Drive Remote Setup for Rclone

## Prerequisites

1. **rclone installed**
   ```bash
   # Ubuntu/Debian
   sudo apt install rclone

   # Linux Mint
   sudo apt install rclone

   # macOS
   brew install rclone

   # Windows (choco)
   choco install rclone
   ```

2. **Google Account** with Drive access

## Initial Configuration

### Interactive Setup
```bash
rclone config
```

Follow the prompts:

1. **n** (new remote)
2. Enter name: `gdrive` (or your preferred name)
3. Select storage type: `drive` (Google Drive)
4. Leave client_id and client_secret blank (press Enter)
5. Choose scope: `1` (full access) or `2` (read-only)
6. Leave root_folder_id blank (press Enter)
7. Leave service_account_file blank (press Enter)
8. Choose advanced config: `n` (unless you need special options)
9. Use auto config? `y` (opens browser for authentication)
10. Confirm remote setup: `y`
11. Quit config: `q`

### Non-Interactive Setup (headless)
For servers without browser:
```bash
rclone config create gdrive drive \
  --client-id "YOUR_CLIENT_ID" \
  --client-secret "YOUR_CLIENT_SECRET" \
  --scope "drive" \
  --root-folder-id "" \
  --config-auth-url "http://localhost:53682/" \
  --config-token-url "http://localhost:53682/" \
  --config-auth-no-open-browser
```

Then visit the provided URL to authenticate.

## Verification

```bash
# List remotes
rclone listremotes

# Test connection
rclone lsd gdrive:

# List root contents
rclone ls gdrive:
```

## Team Drive / Shared Drive Setup

If using Google Workspace shared drives:

```bash
rclone config
```

When prompted for "team drive", enter `y` and select from list.

Or non-interactive:
```bash
rclone config create gdrive-team drive \
  --team-drive "TEAM_DRIVE_ID" \
  --drive-shared-with-me
```

## Authentication Refresh

Tokens expire periodically. Refresh with:

```bash
# Re-authenticate
rclone config reconnect gdrive:

# Or redo entire config
rclone config delete gdrive
rclone config
```

## Multiple Google Accounts

Create separate remotes:
```bash
rclone config create gdrive-personal drive
rclone config create gdrive-work drive
```

Use with `--config` flag if needed:
```bash
rclone lsd gdrive-personal:
rclone lsd gdrive-work:
```

## Security Considerations

### Config File Location
- Default: `~/.config/rclone/rclone.conf`
- Encrypt sensitive data:
  ```bash
  rclone config encrypt ~/.config/rclone/rclone.conf
  ```

### Access Tokens
- Tokens stored in config file
- Revoke access via Google Account → Security → Third-party apps
- Use service accounts for server applications

### Rate Limiting
Google Drive has daily limits:
- 750 GB upload per day
- 10,000,000 files per day

Monitor with:
```bash
rclone about gdrive:
```

## Troubleshooting

### "Failed to create file system"
- Check internet connection
- Verify authentication: `rclone config reconnect gdrive:`
- Check config file permissions

### "User rate limit exceeded"
- Wait before retrying
- Use `--tpslimit 1` to reduce requests
- Consider using service account

### "Permission denied"
- Ensure Google Drive API is enabled
- Check scope permissions
- Verify shared drive access

### Browser doesn't open (headless)
```bash
# Copy the URL from terminal and open manually
rclone config reconnect gdrive: --auto-confirm
```

## Advanced Configuration

### Custom Client ID/Secret
1. Create project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Drive API
3. Create OAuth 2.0 credentials
4. Use in rclone:
   ```bash
   rclone config create gdrive-custom drive \
     --client-id "YOUR_ID.apps.googleusercontent.com" \
     --client-secret "YOUR_SECRET"
   ```

### Service Account (recommended for servers)
1. Create service account in Google Cloud Console
2. Download JSON key file
3. Share Google Drive folder with service account email
4. Configure:
   ```bash
   rclone config create gdrive-sa drive \
     --service-account-file /path/to/key.json
   ```

### Mount Options
```bash
# Install fuse first
sudo apt install fuse

# Mount Google Drive
mkdir ~/gdrive
rclone mount gdrive: ~/gdrive/ --daemon --vfs-cache-mode writes

# Unmount
fusermount -u ~/gdrive
```

## Quick Test

After setup, run:
```bash
# Create test directory
rclone mkdir gdrive:test-rclone

# Copy test file
echo "Test" > /tmp/test.txt
rclone copy /tmp/test.txt gdrive:test-rclone/

# Verify
rclone ls gdrive:test-rclone/

# Cleanup
rclone deletefile gdrive:test-rclone/test.txt
rclone rmdir gdrive:test-rclone
```