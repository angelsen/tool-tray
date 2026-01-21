import subprocess
import threading
from dataclasses import dataclass
from typing import Any

import pystray
from PIL import Image, ImageDraw

from tool_tray.config import config_exists, load_config
from tool_tray.manifest import Manifest, fetch_manifest
from tool_tray.setup_dialog import show_setup_dialog
from tool_tray.updater import get_installed_version, get_remote_version, install_tool


@dataclass
class ToolStatus:
    repo: str
    manifest: Manifest
    installed: str | None
    remote: str | None
    executable: str | None = None

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def has_update(self) -> bool:
        if not self.installed or not self.remote:
            return False
        return self.installed != self.remote

    @property
    def display_text(self) -> str:
        if not self.installed:
            return f"{self.name} (not installed)"
        if self.has_update:
            return f"{self.name} {self.installed} -> {self.remote}"
        return f"{self.name} {self.installed}"

    @property
    def can_launch(self) -> bool:
        return self.executable is not None and self.manifest.launch is not None


_token: str = ""
_repos: list[str] = []
_tool_statuses: list[ToolStatus] = []
_icon: Any = None


def create_icon() -> Image.Image:
    """Create a simple tray icon."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([8, 8, 56, 56], radius=8, fill="#2563eb")
    draw.text((22, 12), "T", fill="white", font_size=36)
    return img


def get_tool_executable(tool_name: str) -> str | None:
    """Get executable path from uv tool list --show-paths."""
    try:
        result = subprocess.run(
            ["uv", "tool", "list", "--show-paths"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith(f"- {tool_name} "):
                start = line.find("(")
                end = line.find(")")
                if start != -1 and end != -1:
                    return line[start + 1 : end]
        return None
    except subprocess.CalledProcessError:
        return None


def launch_tool(tool_name: str) -> None:
    """Launch a tool by name."""
    from tool_tray.logging import log_error, log_info

    for status in _tool_statuses:
        if status.name == tool_name and status.executable:
            log_info(f"Launching: {tool_name} -> {status.executable}")
            try:
                subprocess.Popen([status.executable])
            except OSError as e:
                log_error(f"Failed to launch {tool_name}", e)
            break


def reload_config() -> bool:
    """Reload config from disk. Returns True if config exists."""
    global _token, _repos

    config = load_config()
    if not config:
        _token = ""
        _repos = []
        return False

    _token = config.get("token", "")
    _repos = config.get("repos", [])
    return True


def refresh_statuses() -> None:
    """Refresh version info for all repos with manifests."""
    from tool_tray.logging import log_debug, log_info

    global _tool_statuses
    _tool_statuses = []

    log_info(f"Refreshing {len(_repos)} repos")
    for repo in _repos:
        manifest = fetch_manifest(repo, _token)
        if not manifest:
            continue  # Skip repos without tooltray.toml

        # Get launch command for executable lookup
        launch_cmd = manifest.launch or manifest.name
        installed = get_installed_version(launch_cmd)
        remote = get_remote_version(repo, _token) if _token else None
        executable = get_tool_executable(launch_cmd) if installed else None

        _tool_statuses.append(
            ToolStatus(
                repo=repo,
                manifest=manifest,
                installed=installed,
                remote=remote,
                executable=executable,
            )
        )
        log_debug(f"Status: {manifest.name} installed={installed} remote={remote}")

    log_info(f"Refresh complete: {len(_tool_statuses)} tools loaded")


def update_all() -> None:
    """Install/update all tools with available updates."""
    if not _token:
        return
    for status in _tool_statuses:
        if status.has_update or not status.installed:
            install_tool(status.repo, status.manifest, _token)
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


def on_quit(icon: Any, item: Any) -> None:
    icon.stop()


def make_tool_callback(tool_name: str) -> Any:
    """Create a callback for launching a tool."""

    def callback(icon: Any, item: Any) -> None:
        launch_tool(tool_name)

    return callback


def build_menu() -> Any:
    """Build the tray menu."""
    items: list[Any] = []

    if not _token:
        items.append(pystray.MenuItem("[!] Not configured", None, enabled=False))
        items.append(pystray.MenuItem("Run: tooltray setup", None, enabled=False))
        items.append(pystray.Menu.SEPARATOR)

    for status in _tool_statuses:
        text = status.display_text
        if status.has_update:
            text += " *"
        if status.can_launch:
            items.append(
                pystray.MenuItem(
                    f"> {text}",
                    make_tool_callback(status.name),
                )
            )
        else:
            items.append(pystray.MenuItem(text, None, enabled=False))

    if not _tool_statuses and _token:
        items.append(
            pystray.MenuItem("No tools with tooltray.toml", None, enabled=False)
        )

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
    items.append(pystray.MenuItem("Quit", on_quit))

    return pystray.Menu(*items)


def on_startup(icon: Any) -> None:
    """Called when tray icon is ready."""
    icon.visible = True
    check_for_updates()


def run_tray() -> None:
    """Main entry point - create and run the tray icon."""
    from tool_tray import __version__
    from tool_tray.logging import log_info

    global _icon

    log_info(f"Starting tooltray v{__version__}")

    # Show setup dialog if no config exists
    if not config_exists():
        log_info("No config found, showing setup")
        if not show_setup_dialog():
            log_info("Setup cancelled, exiting")
            return

    reload_config()
    refresh_statuses()

    log_info("Tray icon starting")
    _icon = pystray.Icon(
        "tooltray",
        icon=create_icon(),
        title="Tool Tray",
        menu=build_menu(),
    )
    _icon.run(setup=on_startup)
