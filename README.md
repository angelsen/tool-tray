# Tool Tray

System tray app to manage and update Python tools from private GitHub repos via uv.

## Quick Start

### For Users

1. Install:
   ```bash
   uv tool install tool-tray
   ```

2. Run setup:
   ```bash
   tooltray setup
   ```

3. Paste the config code when prompted

4. Run the tray:
   ```bash
   tooltray
   ```

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
| `tooltray encode` | Generate config code for sharing |
| `tooltray autostart` | Manage system startup |
| `tooltray desktop-icon` | Create desktop shortcuts |
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

### Desktop Icons

```bash
# Requires: uv tool install tool-tray[desktop]
tooltray desktop-icon databridge
```

## Tray Menu

| Item | Description |
|------|-------------|
| `> myapp 1.0.0` | Click to launch |
| `> myapp 1.0.0 -> 1.1.0 *` | Update available, click to launch |
| `myapp (not installed)` | Not yet installed |
| Update All | Install/update all tools |
| Check for Updates | Refresh version info |
| Quit | Exit the app |

## Project Manifest (`tooltray.toml`)

Each managed repo must have a `tooltray.toml` in its root:

```toml
name = "databridge"           # Display name (required)
type = "uv"                   # uv | git | curl (required)
launch = "databridge"         # Command to launch (optional)
build = "npm install"         # Build command for git/curl (optional)
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

Optional:
- `pyshortcuts` for desktop icons (`uv tool install tool-tray[desktop]`)

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
