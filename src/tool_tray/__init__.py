__version__ = "0.2.3"


def main() -> None:
    import sys

    args = sys.argv[1:]

    if not args:
        # Default: run tray app
        from tool_tray.tray import run_tray

        run_tray()
        return

    command = args[0]

    if command == "encode":
        _cmd_encode(args[1:])
    elif command == "setup":
        _cmd_setup()
    elif command == "reset":
        _cmd_reset()
    elif command == "init":
        _cmd_init()
    elif command == "autostart":
        _cmd_autostart(args[1:])
    elif command == "desktop-icon":
        _cmd_desktop_icon(args[1:])
    elif command == "logs":
        _cmd_logs(args[1:])
    elif command in ("-h", "--help", "help"):
        _cmd_help()
    elif command in ("-v", "--version", "version"):
        print(f"tooltray {__version__}")
    else:
        print(f"Unknown command: {command}")
        print("Run 'tooltray --help' for usage")
        sys.exit(1)


def _cmd_help() -> None:
    print("""Tool Tray - System tray tool manager

Usage:
  tooltray                      Run system tray app
  tooltray setup                Configure via CLI (paste config code)
  tooltray reset                Remove config and start fresh
  tooltray init                 Create tooltray.toml in current directory
  tooltray encode               Generate config code for sharing
  tooltray autostart            Manage system autostart
  tooltray desktop-icon         Create desktop shortcuts
  tooltray logs                 View log file

Encode options:
  --token TOKEN                 GitHub PAT (required)
  --repo ORG/REPO               Repository to include (can be repeated)
  --prefix PREFIX               Code prefix for branding (default: TB)

Autostart options:
  --enable                      Add tooltray to system startup
  --disable                     Remove from system startup
  --status                      Check if autostart is enabled

Desktop icon options:
  <toolname>                    Create desktop icon for tool

Logs options:
  -f, --follow                  Tail log file (like tail -f)
  --path                        Print log file path

Examples:
  tooltray setup
  tooltray encode --token ghp_xxx --repo myorg/myapp --repo myorg/cli
  tooltray autostart --enable
  tooltray desktop-icon databridge
""")


def _cmd_setup() -> None:
    from tool_tray.setup_dialog import show_setup_dialog

    if show_setup_dialog():
        print("Configuration saved successfully!")
    else:
        print("Setup cancelled")


def _cmd_reset() -> None:
    from tool_tray.config import get_config_path

    path = get_config_path()
    if not path.exists():
        print("No config found")
        return

    print(f"Config file: {path}")
    try:
        confirm = input("Remove config? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if confirm == "y":
        path.unlink()
        print("Config removed")
    else:
        print("Cancelled")


def _cmd_init() -> None:
    from pathlib import Path

    manifest_path = Path("tooltray.toml")
    if manifest_path.exists():
        print(f"Already exists: {manifest_path}")
        return

    template = """name = ""      # Display name in tray menu
type = "uv"    # uv | git | curl
launch = ""    # Command to run when clicked
"""

    manifest_path.write_text(template)

    print("""tooltray.toml created!

Tool Tray is a system tray app that manages tools from private GitHub repos.
Users get a config code with repo list + token, tooltray fetches manifests.

Edit tooltray.toml:
  name   - Display name in the tray menu
  type   - "uv" for Python tools, "git" for clone+build, "curl" for downloads
  launch - Command name to run when clicked (usually same as name)

Optional fields:
  build        - Build command for git/curl types (e.g. "npm install")
  desktop_icon - Set to true to create desktop shortcut
  autostart    - Set to true to launch on system startup
  icon         - Path to icon file in repo

Once configured, commit tooltray.toml to your repo.
""")


def _cmd_autostart(args: list[str]) -> None:
    import sys

    from tool_tray.autostart import (
        disable_autostart,
        enable_autostart,
        is_autostart_enabled,
    )

    if not args:
        print("Usage: tooltray autostart [--enable|--disable|--status]")
        sys.exit(1)

    option = args[0]
    if option == "--enable":
        if enable_autostart():
            print("Autostart enabled")
        else:
            sys.exit(1)
    elif option == "--disable":
        if disable_autostart():
            print("Autostart disabled")
        else:
            sys.exit(1)
    elif option == "--status":
        if is_autostart_enabled():
            print("Autostart: enabled")
        else:
            print("Autostart: disabled")
    else:
        print(f"Unknown option: {option}")
        print("Usage: tooltray autostart [--enable|--disable|--status]")
        sys.exit(1)


def _cmd_desktop_icon(args: list[str]) -> None:
    import sys

    from tool_tray.desktop import create_desktop_icon

    if not args:
        print("Usage: tooltray desktop-icon <toolname>")
        sys.exit(1)

    tool_name = args[0]
    if not create_desktop_icon(tool_name):
        sys.exit(1)


def _cmd_logs(args: list[str]) -> None:
    import subprocess
    import sys

    from tool_tray.logging import get_log_dir

    log_file = get_log_dir() / "tooltray.log"

    if "--path" in args:
        print(log_file)
        return

    if not log_file.exists():
        print(f"No log file yet: {log_file}")
        sys.exit(1)

    if "-f" in args or "--follow" in args:
        try:
            subprocess.run(["tail", "-f", str(log_file)])
        except KeyboardInterrupt:
            pass
    else:
        subprocess.run(["tail", "-50", str(log_file)])


def _cmd_encode(args: list[str]) -> None:
    import sys

    from tool_tray.config import encode_config

    token = ""
    prefix = "TB"
    repos: list[str] = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--token" and i + 1 < len(args):
            token = args[i + 1]
            i += 2
        elif arg == "--prefix" and i + 1 < len(args):
            prefix = args[i + 1]
            i += 2
        elif arg == "--repo" and i + 1 < len(args):
            repo = args[i + 1]
            if "/" not in repo:
                print(f"Invalid repo format: {repo}")
                print("Expected: ORG/REPO (e.g., myorg/myapp)")
                sys.exit(1)
            repos.append(repo)
            i += 2
        else:
            print(f"Unknown option: {arg}")
            sys.exit(1)

    if not token:
        print("Error: --token is required")
        sys.exit(1)

    if not repos:
        print("Error: at least one --repo is required")
        sys.exit(1)

    code = encode_config(token, repos, prefix)
    print(code)
