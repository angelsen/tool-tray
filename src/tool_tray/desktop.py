import subprocess
from pathlib import Path


def get_tool_executable(tool_name: str) -> Path | None:
    """Get executable path from uv tool list --show-paths."""
    try:
        result = subprocess.run(
            ["uv", "tool", "list", "--show-paths"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            # Format: "- toolname (/path/to/exe)"
            if line.startswith(f"- {tool_name} "):
                start = line.find("(")
                end = line.find(")")
                if start != -1 and end != -1:
                    return Path(line[start + 1 : end])
        return None
    except subprocess.CalledProcessError:
        return None


def create_desktop_icon(tool_name: str, icon_path: str | None = None) -> bool:
    """Create desktop shortcut for a uv tool.

    Args:
        tool_name: Name of the installed tool
        icon_path: Optional path to icon file

    Returns:
        True if shortcut was created successfully
    """
    try:
        from pyshortcuts import make_shortcut
    except ImportError:
        print("pyshortcuts not installed.")
        print("Install with: uv tool install tool-tray[desktop]")
        return False

    exe = get_tool_executable(tool_name)
    if not exe:
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
        print(f"Desktop icon created for '{tool_name}'")
        return True
    except Exception as e:
        print(f"Failed to create desktop icon: {e}")
        return False


def remove_desktop_icon(tool_name: str) -> bool:
    """Remove desktop shortcut for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        True if shortcut was removed successfully
    """
    import sys

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
            print(f"Desktop icon removed for '{tool_name}'")
            return True
        except OSError as e:
            print(f"Failed to remove desktop icon: {e}")
            return False
    else:
        print(f"No desktop icon found for '{tool_name}'")
        return False
