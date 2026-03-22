---
name: rtk-token-optimizer
description: Integrate RTK (Rust Token Killer) CLI proxy to reduce LLM token consumption by 60-90% on common development commands. Use when executing shell commands via OpenClaw to minimize token usage for git, file operations, testing, linting, and container management. Especially valuable for long-running sessions with frequent command execution.
---

# RTK Token Optimizer

## Overview

RTK (Rust Token Killer) is a high-performance CLI proxy that reduces LLM token consumption by 60-90% on common development commands. This skill enables OpenClaw agents to use RTK transparently, filtering and compressing command outputs before they reach the LLM context, dramatically reducing token usage without losing essential information.

## Quick Start

### Installation Verification

Before using RTK, verify it's installed and working:

```bash
rtk --version  # Should show rtk 0.22.2 or later
rtk gain       # Shows token savings statistics (empty initially)
```

If not installed, install via:

```bash
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
```

### Basic Usage Pattern

Prefix common commands with `rtk` when executing via `exec`:

```bash
# Instead of: exec { command: "git status" }
# Use: exec { command: "rtk git status" }

rtk git status      # Compact git status
rtk ls .            # Token-optimized directory tree
rtk grep "pattern" . # Grouped search results
rtk docker ps       # Compact container list
rtk cargo test      # Show failures only (-90% tokens)
```

### Integration with OpenClaw

OpenClaw doesn't have automatic hook system like Claude Code, but you can adopt these patterns:

1. **Manual Prefixing**: Always prepend `rtk` to eligible commands in `exec` calls.
2. **Alias Script**: Create a wrapper script that automatically adds `rtk` to known commands.
3. **Agent Habit**: Train yourself to use `rtk` for commands that produce verbose output.

## Supported Commands

RTK handles numerous command categories with smart filtering:

### Git Operations
- `rtk git status`, `rtk git log -n 10`, `rtk git diff`, `rtk git push`
- Saves 80-92% tokens on git operations

### File Operations
- `rtk ls .`, `rtk read file.rs`, `rtk find "*.rs" .`, `rtk grep "pattern" .`
- Saves 70-80% tokens

### Testing & Linting
- `rtk cargo test`, `rtk pytest`, `rtk ruff check`, `rtk go test`
- Saves 80-90% tokens by showing failures only

### Container Management
- `rtk docker ps`, `rtk docker logs <container>`, `rtk kubectl pods`
- Saves 80% tokens via compact listing

### Package Managers
- `rtk pip list`, `rtk npm test`, `rtk cargo build`
- Saves 70-90% tokens

### GitHub CLI
- `rtk gh pr list`, `rtk gh issue list`, `rtk gh run list`
- Saves 70-80% tokens

## Advanced Features

### Token Savings Analytics

Track your token savings over time:

```bash
rtk gain              # Summary stats
rtk gain --graph      # ASCII graph of last 30 days
rtk gain --history    # Recent command history
rtk gain --daily      # Day-by-day breakdown
```

### Tee: Full Output Recovery

When RTK filters output, you can recover full unfiltered output from failure logs:

```bash
# On command failure, RTK writes full output to ~/.local/share/rtk/tee/
# The agent can read this file instead of re-executing the command
cat ~/.local/share/rtk/tee/1707753600_cargo_test.log
```

### Discover Missed Savings

Find commands where RTK would have saved tokens:

```bash
rtk discover          # Current project, last 30 days
rtk discover --all    # All Claude Code projects
```

## Configuration

### Custom Database Path

Override default tracking database location:

```bash
export RTK_DB_PATH="/path/to/custom.db"
```

Or set in `~/.config/rtk/config.toml`:

```toml
[tracking]
database_path = "/path/to/custom.db"
```

### Tee Configuration

Configure tee behavior in `~/.config/rtk/config.toml`:

```toml
[tee]
enabled = true           # default: true
mode = "failures"        # "failures" (default), "always", or "never"
max_files = 20           # max files to keep
max_file_size = 1048576  # 1MB per file max
```

## Performance Impact

RTK adds minimal overhead (1-5ms per command) while providing:

- **60-90% token reduction** on common operations
- **Zero loss of essential information** (failures, errors, critical output)
- **Smart filtering** removes noise (boilerplate, progress bars, duplicates)
- **Grouping and truncation** maintains context while reducing volume

## Best Practices

1. **Start with high-token commands**: Prioritize `git status`, `cargo test`, `docker ps` for maximum savings.
2. **Monitor savings**: Use `rtk gain` weekly to track impact.
3. **Combine with other optimizations**: Use RTK alongside efficient prompt design and context management.
4. **Teach subagents**: When spawning subagents, include RTK usage in their instructions.

## Troubleshooting

### RTK command not found
- Ensure `~/.local/bin` is in PATH
- Verify installation with `rtk --version`
- Reinstall via curl script if needed

### No token savings reported
- Run `rtk gain` after executing several `rtk` commands
- Check that commands are being prefixed with `rtk`
- Verify command is supported (see supported commands list)

### Hook installation (Claude Code only)
If using Claude Code alongside OpenClaw, consider installing RTK hook:

```bash
rtk init -g  # Global hook installation
```

This automatically rewrites commands in Claude Code sessions.

## Resources

This skill includes no bundled resources as RTK is a standalone binary. For detailed documentation, visit:
- [RTK GitHub Repository](https://github.com/rtk-ai/rtk)
- [RTK Website](https://www.rtk-ai.app)
- [Installation Guide](https://github.com/rtk-ai/rtk/blob/master/INSTALL.md)

---

*Integrating RTK with OpenClaw can reduce token consumption by 60-90%, extending session longevity and reducing costs while maintaining full functionality.*