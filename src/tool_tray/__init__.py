__version__ = "0.1.1"


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
  tooltray                Run system tray app (shows setup if not configured)
  tooltray setup          Re-run setup dialog
  tooltray encode         Generate config code for sharing

Encode options:
  --token TOKEN          GitHub PAT (required)
  --tool NAME:REPO       Tool to include (can be repeated)
  --prefix PREFIX        Code prefix for branding (default: TB)

Examples:
  tooltray encode --token ghp_xxx --tool myapp:myorg/myapp
  tooltray encode --token ghp_xxx --tool cli:acme/cli --tool api:acme/api
  tooltray encode --prefix ACME --token ghp_xxx --tool cli:acme/cli
""")


def _cmd_setup() -> None:
    from tool_tray.setup_dialog import show_setup_dialog

    if show_setup_dialog():
        print("Configuration saved successfully!")
    else:
        print("Setup cancelled")


def _cmd_encode(args: list[str]) -> None:
    import sys

    from tool_tray.config import encode_config

    token = ""
    prefix = "TB"
    tools: list[dict] = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--token" and i + 1 < len(args):
            token = args[i + 1]
            i += 2
        elif arg == "--prefix" and i + 1 < len(args):
            prefix = args[i + 1]
            i += 2
        elif arg == "--tool" and i + 1 < len(args):
            tool_spec = args[i + 1]
            if ":" not in tool_spec:
                print(f"Invalid tool format: {tool_spec}")
                print(
                    "Expected: NAME:ORG/REPO (e.g., myapp:myorg/myapp)"
                )
                sys.exit(1)
            name, repo = tool_spec.split(":", 1)
            tools.append({"name": name, "repo": repo})
            i += 2
        else:
            print(f"Unknown option: {arg}")
            sys.exit(1)

    if not token:
        print("Error: --token is required")
        sys.exit(1)

    if not tools:
        print("Error: at least one --tool is required")
        sys.exit(1)

    code = encode_config(token, tools, prefix)
    print(code)
