import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pystray
from PIL import Image, ImageDraw

from tool_tray.config import config_exists, load_config
from tool_tray.manifest import Manifest, fetch_manifest
from tool_tray.updater import get_installed_version, get_remote_version, install_tool


@dataclass
class OrphanedIcon:
    """A desktop icon that should be cleaned up."""

    tool_name: str
    path: str
    reason: str  # "tool_removed", "desktop_icon_disabled", "file_missing"


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
_last_refresh: float = 0
_REFRESH_THROTTLE_SECONDS: int = 30


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


def refresh_statuses(force: bool = False) -> None:
    """Refresh version info for all repos with manifests."""
    import time

    from tool_tray.logging import log_debug, log_info

    global _tool_statuses, _last_refresh

    # Throttle refreshes to avoid hitting GitHub API repeatedly
    now = time.time()
    if (
        not force
        and _last_refresh
        and (now - _last_refresh) < _REFRESH_THROTTLE_SECONDS
    ):
        log_debug(f"Refresh throttled ({int(now - _last_refresh)}s since last)")
        return

    _tool_statuses = []
    _last_refresh = now

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


def find_orphaned_icons() -> list[OrphanedIcon]:
    """Find desktop icons that should be cleaned up. Called each time menu opens."""
    from tool_tray.state import load_state

    orphans: list[OrphanedIcon] = []

    state = load_state()
    if not state.desktop_icons:
        return orphans

    # Build set of active repos and their manifests
    active_repos = set(_repos)
    manifest_by_repo: dict[str, Manifest] = {}
    for status in _tool_statuses:
        manifest_by_repo[status.repo] = status.manifest

    for tool_name, record in state.desktop_icons.items():
        icon_path = Path(record.path)

        # Check if file was deleted externally
        if not icon_path.exists():
            orphans.append(
                OrphanedIcon(
                    tool_name=tool_name,
                    path=record.path,
                    reason="file_missing",
                )
            )
            continue

        # Check if repo was removed from config
        if record.repo not in active_repos:
            orphans.append(
                OrphanedIcon(
                    tool_name=tool_name,
                    path=record.path,
                    reason="tool_removed",
                )
            )
            continue

        # Check if desktop_icon was disabled in manifest
        manifest = manifest_by_repo.get(record.repo)
        if manifest and not manifest.desktop_icon:
            orphans.append(
                OrphanedIcon(
                    tool_name=tool_name,
                    path=record.path,
                    reason="desktop_icon_disabled",
                )
            )

    return orphans


def cleanup_orphans(orphans: list[OrphanedIcon]) -> int:
    """Remove orphaned icons. Returns count of removed icons."""
    from tool_tray.desktop import remove_desktop_icon
    from tool_tray.logging import log_info
    from tool_tray.state import remove_icon_record

    count = 0

    for orphan in orphans:
        if orphan.reason == "file_missing":
            # Just remove the record
            remove_icon_record(orphan.tool_name)
            count += 1
        else:
            # Remove file and record
            if remove_desktop_icon(orphan.tool_name):
                remove_icon_record(orphan.tool_name)
                count += 1

    if count:
        log_info(f"Cleaned up {count} orphaned icons")

    return count


def update_all() -> None:
    """Install/update all tools with available updates."""
    if not _token:
        return
    for status in _tool_statuses:
        if status.has_update or not status.installed:
            install_tool(status.repo, status.manifest, _token)


def on_update_all(icon: Any, item: Any) -> None:
    """Install/update all tools in background."""
    threading.Thread(target=update_all, daemon=True).start()


def make_cleanup_callback(orphans: list[OrphanedIcon]) -> Any:
    """Create a callback that cleans up the given orphans."""

    def callback(icon: Any, item: Any) -> None:
        cleanup_orphans(orphans)

    return callback


def on_quit(icon: Any, item: Any) -> None:
    icon.stop()


def make_tool_callback(tool_name: str) -> Any:
    """Create a callback for launching a tool."""

    def callback(icon: Any, item: Any) -> None:
        launch_tool(tool_name)

    return callback


def build_menu_items() -> list[Any]:
    """Build menu items from current state. Called each time menu opens."""
    # Reload config and statuses fresh each time menu opens
    reload_config()
    if _token:
        refresh_statuses()

    items: list[Any] = []

    # Not configured state
    if not _token:
        items.append(pystray.MenuItem("[!] Not configured", None, enabled=False))
        items.append(pystray.MenuItem("Setup...", on_configure))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Quit", on_quit))
        return items

    # Configured state - show tools
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

    if not _tool_statuses:
        items.append(
            pystray.MenuItem("No tools with tooltray.toml", None, enabled=False)
        )

    # Show orphaned icons section if any exist
    orphans = find_orphaned_icons()
    if orphans:
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Orphaned Icons:", None, enabled=False))
        for orphan in orphans:
            reason_text = {
                "tool_removed": "repo removed",
                "desktop_icon_disabled": "disabled",
                "file_missing": "file missing",
            }.get(orphan.reason, orphan.reason)
            items.append(
                pystray.MenuItem(
                    f"  {orphan.tool_name} ({reason_text})", None, enabled=False
                )
            )
        items.append(
            pystray.MenuItem(
                f"Clean Up ({len(orphans)})",
                make_cleanup_callback(orphans),
            )
        )

    items.append(pystray.Menu.SEPARATOR)

    has_updates = any(s.has_update or not s.installed for s in _tool_statuses)
    items.append(
        pystray.MenuItem(
            "Update All",
            on_update_all,
            enabled=has_updates,
        )
    )
    items.append(pystray.MenuItem("Configure...", on_configure))
    items.append(pystray.Menu.SEPARATOR)
    items.append(pystray.MenuItem("Quit", on_quit))

    return items


def build_menu() -> Any:
    """Build dynamic menu that rebuilds items each time it's opened."""
    return pystray.Menu(lambda: iter(build_menu_items()))


def on_startup(icon: Any) -> None:
    """Called when tray icon is ready."""
    icon.visible = True
    refresh_statuses()


def spawn_setup() -> None:
    """Spawn setup dialog as subprocess."""
    import shutil
    import sys

    from tool_tray.logging import log_info

    # Use tooltray script (not -m) because tkinter needs proper Tcl/Tk paths
    tooltray_bin = shutil.which("tooltray") or sys.argv[0]
    cmd = [tooltray_bin, "setup"]
    log_info(f"Spawning setup subprocess: {cmd}")
    subprocess.Popen(cmd)


def on_configure(icon: Any, item: Any) -> None:
    """Open setup dialog for configuration."""
    spawn_setup()


def run_tray() -> None:
    """Main entry point - create and run the tray icon."""
    from tool_tray import __version__
    from tool_tray.logging import log_info

    global _icon

    log_info(f"Starting tooltray v{__version__}")

    # Spawn setup dialog if no config (non-blocking)
    if not config_exists():
        log_info("No config found, spawning setup")
        spawn_setup()

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
