import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from tool_tray.config import get_config_dir


@dataclass
class DesktopIconRecord:
    """Record of a desktop icon we created."""

    path: str
    tool_name: str
    created_at: str
    repo: str


@dataclass
class State:
    """Application state persisted to disk."""

    version: int = 1
    desktop_icons: dict[str, DesktopIconRecord] = field(default_factory=dict)


def get_state_path() -> Path:
    """Get path to state.json (same directory as config)."""
    return get_config_dir() / "state.json"


def load_state() -> State:
    """Load state from disk, returning empty state if not found."""
    from tool_tray.logging import log_debug, log_error

    path = get_state_path()
    if not path.exists():
        log_debug(f"State not found: {path}")
        return State()

    try:
        data = json.loads(path.read_text())
        icons: dict[str, DesktopIconRecord] = {}
        for key, record in data.get("desktop_icons", {}).items():
            icons[key] = DesktopIconRecord(
                path=record["path"],
                tool_name=record["tool_name"],
                created_at=record["created_at"],
                repo=record["repo"],
            )
        log_debug(f"State loaded: {len(icons)} desktop icons")
        return State(version=data.get("version", 1), desktop_icons=icons)
    except (json.JSONDecodeError, OSError, KeyError) as e:
        log_error(f"Failed to load state: {path}", e)
        return State()


def save_state(state: State) -> None:
    """Save state to disk."""
    from tool_tray.logging import log_debug

    path = get_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "version": state.version,
        "desktop_icons": {
            key: {
                "path": record.path,
                "tool_name": record.tool_name,
                "created_at": record.created_at,
                "repo": record.repo,
            }
            for key, record in state.desktop_icons.items()
        },
    }
    path.write_text(json.dumps(data, indent=2))
    log_debug(f"State saved: {len(state.desktop_icons)} desktop icons -> {path}")


def record_desktop_icon(tool_name: str, path: str, repo: str) -> None:
    """Record that we created a desktop icon."""
    from tool_tray.logging import log_debug

    state = load_state()
    state.desktop_icons[tool_name] = DesktopIconRecord(
        path=path,
        tool_name=tool_name,
        created_at=datetime.now().isoformat(),
        repo=repo,
    )
    save_state(state)
    log_debug(f"Recorded desktop icon: {tool_name} -> {path}")


def remove_icon_record(tool_name: str) -> bool:
    """Remove a desktop icon record. Returns True if record existed."""
    from tool_tray.logging import log_debug

    state = load_state()
    if tool_name not in state.desktop_icons:
        return False

    del state.desktop_icons[tool_name]
    save_state(state)
    log_debug(f"Removed icon record: {tool_name}")
    return True
