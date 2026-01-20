# Tool Tray

System tray app to manage and update Python tools from private GitHub repos via uv.

## Quick Start

### For Users

1. Install:
   ```bash
   uv tool install tool-tray
   ```

2. Run:
   ```bash
   tooltray
   ```

3. Paste the config code when prompted

4. Done! The tray icon shows tool versions and updates.

### For Admins

Generate a config code to share with your team:

```bash
tooltray encode --token ghp_xxx --tool myapp:myorg/myapp
# Output: TB-eyJ0b2tlbi...
```

Share the output code via your internal channels.

## Commands

| Command | Description |
|---------|-------------|
| `tooltray` | Run tray app (shows setup if not configured) |
| `tooltray setup` | Re-run setup dialog |
| `tooltray encode` | Generate config code for sharing |
| `tooltray --help` | Show help |
| `tooltray --version` | Show version |

### Encode Options

```bash
tooltray encode --token TOKEN --tool NAME:ORG/REPO [--tool ...] [--prefix PREFIX]
```

Examples:
```bash
# Single tool (default TB- prefix)
tooltray encode --token ghp_xxx --tool myapp:myorg/myapp

# Multiple tools
tooltray encode --token ghp_xxx \
  --tool cli:acme/cli \
  --tool api:acme/api

# Custom prefix for branding
tooltray encode --prefix ACME --token ghp_xxx --tool cli:acme/cli
```

## Tray Menu

| Item | Description |
|------|-------------|
| `myapp 1.0.0 → 1.1.0 ⬆` | Update available |
| `myapp 1.0.0` | Up to date |
| `myapp (not installed)` | Not yet installed |
| Update All | Install/update all tools |
| Check for Updates | Refresh version info |
| Setup... | Re-paste config code |
| Quit | Exit the app |

## Config Code Format

The config code is a prefix + base64-encoded JSON with the GitHub token and tool list:

```
TB-eyJ0b2tlbiI6ImdocF94eHgiLCJ0b29scyI6W3sibmFtZSI6Im15YXBwIiwicmVwbyI6Im15b3JnL215YXBwIn1dfQ==
```

Decodes to:
```json
{
  "token": "ghp_xxx",
  "tools": [
    {"name": "myapp", "repo": "myorg/myapp"}
  ]
}
```

The prefix (default `TB`) can be customized with `--prefix` for org branding.

Config is stored at:
- **Windows:** `%LOCALAPPDATA%\tooltray\config.json`
- **macOS:** `~/Library/Application Support/tooltray/config.json`
- **Linux:** `~/.config/tooltray/config.json` (or `$XDG_CONFIG_HOME/tooltray/`)

## Requirements

- Python 3.12+
- uv
- tkinter (usually included with Python)

## Architecture

```
Internal channel: "TB-eyJ0b2tlbi..." (config code)
     │
     ▼ (user pastes on first run)
┌─────────────────────────────────┐
│ tooltray (system tray)          │
│ ┌─────────────────────────────┐ │
│ │ 🔧 Tool Tray                │ │
│ │ myapp       1.0.0 → 1.1.0 ⬆ │ │
│ │ Update All                  │ │
│ │ Check for Updates           │ │
│ │ Setup...                    │ │
│ │ Quit                        │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
     │
     ▼ (uv tool install git+https://oauth2:TOKEN@github.com/...)
   Private GitHub Repos
```

## Development

```bash
# Run directly
uv run tooltray

# Test encode command
uv run tooltray encode --token test123 --tool myapp:myorg/myapp
```

## License

MIT
