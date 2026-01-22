# Tool Tray

System tray app to manage and update Python tools from private GitHub repos via uv.

## Quick Start

### For Users

1. Install:
   ```bash
   uv tool install tool-tray
   ```

2. Run the tray:
   ```bash
   tooltray
   ```

3. On first run, setup dialog opens automatically - paste your config code

### For Admins

Generate a config code to share with your team:

```bash
tooltray encode --token ghp_xxx --repo myorg/myapp
# Output: TB-eyJ0b2tlbi...
```

Each repo must have a `tooltray.toml` manifest (see below).

## Commands

| Command | Description |
|---------|-------------|
| `tooltray` | Run tray app |
| `tooltray setup` | Configure via CLI (paste config code) |
| `tooltray reset` | Remove config and start fresh |
| `tooltray init` | Create `tooltray.toml` template in current dir |
| `tooltray encode` | Generate config code for sharing |
| `tooltray autostart` | Manage system startup |
| `tooltray logs` | View log file |
| `tooltray cleanup` | Remove orphaned desktop icons |
| `tooltray --help` | Show help |
| `tooltray --version` | Show version |

### Encode Options

```bash
tooltray encode --token TOKEN --repo ORG/REPO [--repo ...] [--prefix PREFIX]
```

Examples:
```bash
# Single repo (default TB- prefix)
tooltray encode --token ghp_xxx --repo myorg/myapp

# Multiple repos
tooltray encode --token ghp_xxx \
  --repo acme/cli \
  --repo acme/api

# Custom prefix for branding
tooltray encode --prefix ACME --token ghp_xxx --repo acme/cli
```

### Autostart

```bash
tooltray autostart --enable   # Add to system startup
tooltray autostart --disable  # Remove from startup
tooltray autostart --status   # Check if enabled
```

### Logs

```bash
tooltray logs           # Show last 50 lines
tooltray logs -f        # Tail in real-time
tooltray logs --path    # Print log file path
```

### Cleanup

Remove orphaned desktop icons (icons for tools no longer in config):

```bash
tooltray cleanup --dry-run  # Show what would be removed
tooltray cleanup            # Prompt and remove
tooltray cleanup --force    # Remove without prompting
```

## Tray Menu

When not configured:
| Item | Description |
|------|-------------|
| `[!] Not configured` | Status indicator |
| Setup... | Open setup dialog |
| Quit | Exit the app |

When configured:
| Item | Description |
|------|-------------|
| `> myapp 1.0.0` | Click to launch |
| `> myapp 1.0.0 -> 1.1.0 *` | Update available, click to launch |
| `myapp (not installed)` | Not yet installed |
| Orphaned Icons | Shows icons needing cleanup (if any) |
| Clean Up (n) | Remove orphaned icons |
| Update All | Install/update all tools |
| Check for Updates | Refresh version info |
| Configure... | Open setup dialog to reconfigure |
| Quit | Exit the app |

## Project Manifest (`tooltray.toml`)

Each managed repo must have a `tooltray.toml` in its root:

```toml
name = "databridge"           # Display name (required)
type = "uv"                   # uv | git (required)
launch = "databridge"         # Command to launch (optional)
build = "npm install"         # Build command for git type (optional)
desktop_icon = true           # Create desktop shortcut (default: false)
icon = "assets/icon.png"      # Path to icon in repo (optional)
autostart = false             # Add to system autostart (default: false)
```

Repos without `tooltray.toml` are skipped.

## Config Code Format

The config code is a prefix + base64-encoded JSON:

```
TB-eyJ0b2tlbiI6ImdocF94eHgiLCJyZXBvcyI6WyJteW9yZy9teWFwcCJdfQ==
```

Decodes to:
```json
{
  "token": "ghp_xxx",
  "repos": ["myorg/myapp"]
}
```

Config is stored at:
- **Windows:** `%LOCALAPPDATA%\tooltray\config.json`
- **macOS:** `~/Library/Application Support/tooltray/config.json`
- **Linux:** `~/.config/tooltray/config.json`

## Requirements

- Python 3.12+
- uv

## Development

```bash
# Run directly
uv run tooltray

# Test encode command
uv run tooltray encode --token test123 --repo myorg/myapp

# Type check
uv run basedpyright src/
```

## License

MIT
