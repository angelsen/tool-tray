__version__ = "0.2.0"


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
    elif command == "autostart":
        _cmd_autostart(args[1:])
    elif command == "desktop-icon":
        _cmd_desktop_icon(args[1:])
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
  tooltray encode               Generate config code for sharing
  tooltray autostart            Manage system autostart
  tooltray desktop-icon         Create desktop shortcuts

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
