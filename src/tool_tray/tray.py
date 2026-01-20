import threading
from dataclasses import dataclass
from typing import Any

import pystray
from PIL import Image, ImageDraw

from tool_tray.config import config_exists, load_config
from tool_tray.setup_dialog import show_setup_dialog
from tool_tray.tools import Tool
from tool_tray.updater import get_installed_version, get_remote_version, install_tool


@dataclass
class ToolStatus:
    tool: Tool
    installed: str | None
    remote: str | None

    @property
    def has_update(self) -> bool:
        if not self.installed or not self.remote:
            return False
        return self.installed != self.remote

    @property
    def display_text(self) -> str:
        if not self.installed:
            return f"{self.tool.name} (not installed)"
        if self.has_update:
            return f"{self.tool.name} {self.installed} → {self.remote}"
        return f"{self.tool.name} {self.installed}"


_token: str = ""
_tools: list[Tool] = []
_tool_statuses: list[ToolStatus] = []
_icon: Any = None


def create_icon() -> Image.Image:
    """Create a simple wrench icon."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([8, 8, 56, 56], radius=8, fill="#2563eb")
    draw.text((20, 16), "🔧", fill="white")
    return img


def reload_config() -> bool:
    """Reload config from disk. Returns True if config exists."""
    global _token, _tools

    config = load_config()
    if not config:
        _token = ""
        _tools = []
        return False

    _token = config.get("token", "")
    _tools = [Tool.from_dict(t) for t in config.get("tools", [])]
    return True


def refresh_statuses() -> None:
    """Refresh version info for all tools."""
    global _tool_statuses
    _tool_statuses = []
    for tool in _tools:
        installed = get_installed_version(tool.name)
        remote = get_remote_version(tool, _token) if _token else None
        _tool_statuses.append(ToolStatus(tool, installed, remote))


def update_all() -> None:
    """Install/update all tools with available updates."""
    if not _token:
        return
    for status in _tool_statuses:
        if status.has_update or not status.installed:
            install_tool(status.tool, _token)
    refresh_statuses()
    if _icon:
        _icon.update_menu()


def check_for_updates() -> None:
    """Background refresh of version info."""
    refresh_statuses()
    if _icon:
        _icon.update_menu()


def on_check_updates(icon: Any, item: Any) -> None:
    threading.Thread(target=check_for_updates, daemon=True).start()


def on_update_all(icon: Any, item: Any) -> None:
    threading.Thread(target=update_all, daemon=True).start()


def on_setup(icon: Any, item: Any) -> None:
    """Open the setup dialog."""

    def do_setup() -> None:
        if show_setup_dialog():
            reload_config()
            refresh_statuses()
            if _icon:
                _icon.update_menu()

    threading.Thread(target=do_setup, daemon=True).start()


def on_quit(icon: Any, item: Any) -> None:
    icon.stop()


def build_menu() -> Any:
    """Build the tray menu."""
    items: list[Any] = []

    if not _token:
        items.append(pystray.MenuItem("⚠ Not configured", None, enabled=False))
        items.append(pystray.Menu.SEPARATOR)

    for status in _tool_statuses:
        text = status.display_text
        if status.has_update:
            text += " ⬆"
        items.append(pystray.MenuItem(text, None, enabled=False))

    if not _tool_statuses and _token:
        items.append(pystray.MenuItem("No tools configured", None, enabled=False))

    items.append(pystray.Menu.SEPARATOR)

    has_updates = any(s.has_update or not s.installed for s in _tool_statuses)
    items.append(
        pystray.MenuItem(
            "Update All",
            on_update_all,
            enabled=has_updates and bool(_token),
        )
    )
    items.append(
        pystray.MenuItem("Check for Updates", on_check_updates, enabled=bool(_token))
    )
    items.append(pystray.Menu.SEPARATOR)
    items.append(pystray.MenuItem("Setup...", on_setup))
    items.append(pystray.MenuItem("Quit", on_quit))

    return pystray.Menu(*items)


def on_startup(icon: Any) -> None:
    """Called when tray icon is ready."""
    icon.visible = True
    check_for_updates()


def run_tray() -> None:
    """Main entry point - create and run the tray icon."""
    global _icon

    # Show setup dialog if no config exists
    if not config_exists():
        if not show_setup_dialog():
            return  # User cancelled, exit

    reload_config()
    refresh_statuses()

    _icon = pystray.Icon(
        "tooltray",
        icon=create_icon(),
        title="Tool Tray",
        menu=build_menu(),
    )
    _icon.run(setup=on_startup)
