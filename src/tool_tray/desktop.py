from pathlib import Path

from tool_tray.tray import get_tool_executable


def create_desktop_icon(tool_name: str, icon_path: str | None = None) -> bool:
    """Create desktop shortcut for a uv tool."""
    from tool_tray.logging import log_debug, log_error, log_info

    log_debug(f"Creating desktop icon: {tool_name}")

    try:
        from pyshortcuts import make_shortcut
    except ImportError:
        log_debug("pyshortcuts not installed, skipping desktop icon")
        print("pyshortcuts not installed.")
        print("Install with: uv tool install tool-tray[desktop]")
        return False

    exe = get_tool_executable(tool_name)
    if not exe:
        log_error(f"Tool not found for desktop icon: {tool_name}")
        print(f"Tool '{tool_name}' not found in uv tool list")
        return False

    try:
        make_shortcut(
            str(exe),
            name=tool_name.replace("-", " ").title(),
            icon=icon_path,
            terminal=False,
            desktop=True,
        )
        log_info(f"Desktop icon created: {tool_name}")
        print(f"Desktop icon created for '{tool_name}'")
        return True
    except Exception as e:
        log_error(f"Failed to create desktop icon: {tool_name}", e)
        print(f"Failed to create desktop icon: {e}")
        return False


def remove_desktop_icon(tool_name: str) -> bool:
    """Remove desktop shortcut for a tool."""
    import sys

    from tool_tray.logging import log_error, log_info

    display_name = tool_name.replace("-", " ").title()

    if sys.platform == "darwin":
        shortcut = Path.home() / "Desktop" / f"{display_name}.app"
    elif sys.platform == "win32":
        shortcut = Path.home() / "Desktop" / f"{display_name}.lnk"
    else:
        shortcut = Path.home() / "Desktop" / f"{display_name}.desktop"

    if shortcut.exists():
        try:
            if shortcut.is_dir():
                import shutil

                shutil.rmtree(shortcut)
            else:
                shortcut.unlink()
            log_info(f"Desktop icon removed: {tool_name}")
            print(f"Desktop icon removed for '{tool_name}'")
            return True
        except OSError as e:
            log_error(f"Failed to remove desktop icon: {tool_name}", e)
            print(f"Failed to remove desktop icon: {e}")
            return False
    else:
        print(f"No desktop icon found for '{tool_name}'")
        return False
