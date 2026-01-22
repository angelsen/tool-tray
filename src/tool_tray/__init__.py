__version__ = "0.3.7"


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
        _cmd_setup(args[1:])
    elif command == "reset":
        _cmd_reset()
    elif command == "init":
        _cmd_init()
    elif command == "autostart":
        _cmd_autostart(args[1:])
    elif command == "logs":
        _cmd_logs(args[1:])
    elif command == "cleanup":
        _cmd_cleanup(args[1:])
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
  tooltray setup                Configure via GUI dialog
  tooltray reset                Remove config and start fresh
  tooltray init                 Create tooltray.toml in current directory
  tooltray encode               Generate config code for sharing
  tooltray autostart            Manage system autostart
  tooltray logs                 View log file
  tooltray cleanup              Remove orphaned desktop icons

Setup options:
  --code CODE                   Config code (skip GUI dialog)

Encode options:
  --token TOKEN                 GitHub PAT (required)
  --repo ORG/REPO               Repository to include (can be repeated)
  --prefix PREFIX               Code prefix for branding (default: TB)

Autostart options:
  --enable                      Add tooltray to system startup
  --disable                     Remove from system startup
  --status                      Check if autostart is enabled

Logs options:
  -f, --follow                  Tail log file (like tail -f)
  --path                        Print log file path

Cleanup options:
  --dry-run                     Show what would be removed
  --force                       Remove without confirmation

Examples:
  tooltray setup
  tooltray setup --code "TB-eyJ0b2tlbi..."
  tooltray encode --token ghp_xxx --repo myorg/myapp --repo myorg/cli
  tooltray autostart --enable
  tooltray cleanup --dry-run
""")


def _cmd_setup(args: list[str]) -> None:
    from tool_tray.config import decode_config, save_config

    # Check for --code flag
    code: str | None = None
    i = 0
    while i < len(args):
        if args[i] == "--code" and i + 1 < len(args):
            code = args[i + 1]
            break
        i += 1

    if code:
        # Direct CLI mode
        try:
            config = decode_config(code)
            save_config(config)
            print("Configuration saved successfully!")
        except ValueError as e:
            print(f"Error: {e}")
    else:
        # GUI dialog mode
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
type = "uv"    # uv | git
launch = ""    # Command to run when clicked
"""

    manifest_path.write_text(template)

    print("""tooltray.toml created!

Tool Tray is a system tray app that manages tools from private GitHub repos.
Users get a config code with repo list + token, tooltray fetches manifests.

Edit tooltray.toml:
  name   - Display name in the tray menu
  type   - "uv" for Python tools, "git" for clone+build
  launch - Command name to run when clicked (usually same as name)

Optional fields:
  build        - Build command for git type (e.g. "npm install")
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


def _cmd_logs(args: list[str]) -> None:
    import time

    from tool_tray.logging import get_log_dir

    log_file = get_log_dir() / "tooltray.log"

    if "--path" in args:
        print(log_file)
        return

    if not log_file.exists():
        print(f"No log file yet: {log_file}")
        return

    if "-f" in args or "--follow" in args:
        try:
            with open(log_file) as f:
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if line:
                        print(line, end="")
                    else:
                        time.sleep(0.5)
        except KeyboardInterrupt:
            pass
    else:
        lines = log_file.read_text().splitlines()
        for line in lines[-50:]:
            print(line)


def _cmd_cleanup(args: list[str]) -> None:
    from pathlib import Path

    from tool_tray.config import load_config
    from tool_tray.desktop import remove_desktop_icon
    from tool_tray.manifest import fetch_manifest
    from tool_tray.state import load_state, remove_icon_record

    dry_run = "--dry-run" in args
    force = "--force" in args

    # Load config to get active repos
    config = load_config()
    if not config:
        print("No config found. Run 'tooltray setup' first.")
        return

    token = config.get("token", "")
    repos = config.get("repos", [])
    active_repos = set(repos)

    # Build manifest lookup for active repos
    manifest_by_repo: dict[str, bool] = {}  # repo -> desktop_icon enabled
    for repo in repos:
        manifest = fetch_manifest(repo, token)
        if manifest:
            manifest_by_repo[repo] = manifest.desktop_icon

    # Find orphaned icons
    state = load_state()
    orphans: list[tuple[str, str, str]] = []  # (tool_name, path, reason)

    for tool_name, record in state.desktop_icons.items():
        icon_path = Path(record.path)

        if not icon_path.exists():
            orphans.append((tool_name, record.path, "file missing"))
        elif record.repo not in active_repos:
            orphans.append((tool_name, record.path, "repo removed"))
        elif record.repo in manifest_by_repo and not manifest_by_repo[record.repo]:
            orphans.append((tool_name, record.path, "desktop_icon disabled"))

    if not orphans:
        print("No orphaned icons found.")
        return

    # Display orphans
    print(f"Found {len(orphans)} orphaned icon(s):\n")
    for tool_name, path, reason in orphans:
        print(f"  {tool_name}")
        print(f"    Path: {path}")
        print(f"    Reason: {reason}\n")

    if dry_run:
        print("Dry run - no changes made.")
        return

    # Confirm unless --force
    if not force:
        try:
            confirm = input("Remove these icons? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if confirm != "y":
            print("Cancelled")
            return

    # Remove orphans
    removed = 0
    for tool_name, path, reason in orphans:
        if reason == "file missing":
            remove_icon_record(tool_name)
            removed += 1
            print(f"Removed record: {tool_name}")
        else:
            if remove_desktop_icon(tool_name):
                remove_icon_record(tool_name)
                removed += 1
                print(f"Removed: {tool_name}")
            else:
                print(f"Failed to remove: {tool_name}")

    print(f"\nCleaned up {removed} icon(s).")


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
            from urllib.parse import unquote

            repo = unquote(args[i + 1]).strip().strip("'\"")
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
