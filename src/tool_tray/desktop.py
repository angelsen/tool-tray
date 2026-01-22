import contextlib
import io
import os
import sys
from pathlib import Path

from tool_tray.tray import get_tool_executable


def get_desktop_path() -> Path:
    """Get OS-appropriate desktop directory."""
    if sys.platform == "win32":
        desktop = os.environ.get("USERPROFILE", "")
        return Path(desktop) / "Desktop" if desktop else Path.home() / "Desktop"
    elif sys.platform == "darwin":
        return Path.home() / "Desktop"
    else:
        # Linux: check XDG user dirs, fall back to ~/Desktop
        xdg_desktop = os.environ.get("XDG_DESKTOP_DIR")
        if xdg_desktop:
            return Path(xdg_desktop)
        return Path.home() / "Desktop"


def get_desktop_icon_path(tool_name: str) -> Path:
    """Compute where pyshortcuts creates the desktop icon."""
    display_name = tool_name.replace("-", " ").title()

    if sys.platform == "win32":
        return get_desktop_path() / f"{display_name}.lnk"
    elif sys.platform == "darwin":
        return get_desktop_path() / f"{display_name}.app"
    else:
        # Linux: .desktop file
        return get_desktop_path() / f"{display_name}.desktop"


def remove_desktop_icon(tool_name: str) -> bool:
    """Delete desktop icon from disk. Returns True if deleted."""
    from tool_tray.logging import log_debug, log_error, log_info

    path = get_desktop_icon_path(tool_name)
    log_debug(f"Removing desktop icon: {path}")

    if not path.exists():
        log_debug(f"Desktop icon not found: {path}")
        return False

    try:
        if path.is_dir():
            # macOS .app bundles are directories
            import shutil

            shutil.rmtree(path)
        else:
            path.unlink()
        log_info(f"Desktop icon removed: {path}")
        return True
    except OSError as e:
        log_error(f"Failed to remove desktop icon: {path}", e)
        return False


def create_desktop_icon(
    tool_name: str, icon_path: str | None = None, repo: str | None = None
) -> bool:
    """Create desktop shortcut for a uv tool."""
    from tool_tray.logging import log_debug, log_error, log_info

    log_debug(f"Creating desktop icon: {tool_name}")

    from pyshortcuts import make_shortcut

    exe = get_tool_executable(tool_name)
    if not exe:
        log_error(f"Tool not found for desktop icon: {tool_name}")
        return False

    try:
        # Suppress stdout - pyshortcuts has debug prints on macOS
        # noexe=True because uv tool shims are self-contained executables
        with contextlib.redirect_stdout(io.StringIO()):
            make_shortcut(
                str(exe),
                name=tool_name.replace("-", " ").title(),
                icon=icon_path,
                terminal=False,
                desktop=True,
                noexe=True,
            )
        log_info(f"Desktop icon created: {tool_name}")

        # Record the icon in state if repo is provided
        if repo:
            from tool_tray.state import record_desktop_icon

            icon_file = get_desktop_icon_path(tool_name)
            record_desktop_icon(tool_name, str(icon_file), repo)

        return True
    except Exception as e:
        log_error(f"Failed to create desktop icon: {tool_name}", e)
        return False
