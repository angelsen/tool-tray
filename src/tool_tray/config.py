import base64
import json
import os
import sys
from pathlib import Path


def get_config_dir() -> Path:
    """Get OS-appropriate config directory."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "tooltray"
        return Path.home() / "AppData/Local/tooltray"
    elif sys.platform == "darwin":
        return Path.home() / "Library/Application Support/tooltray"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return Path(xdg) / "tooltray"
        return Path.home() / ".config/tooltray"


def get_config_path() -> Path:
    """Get path to config.json."""
    return get_config_dir() / "config.json"


def encode_config(token: str, repos: list[str], prefix: str = "TB") -> str:
    """Encode token and repos into a shareable config code (v2 format).

    Args:
        token: GitHub PAT (ghp_xxx)
        repos: List of "org/repo" strings
        prefix: Code prefix for branding (default: "TB")

    Returns:
        Config code like "TB-eyJ0b2tlbi..."
    """
    data = {"token": token, "repos": repos}
    b64 = base64.b64encode(json.dumps(data).encode()).decode()
    return f"{prefix}-{b64}"


def decode_config(code: str) -> dict:
    """Decode config code back to token and repos.

    Args:
        code: Config code in format "PREFIX-base64data"

    Returns:
        Dict with "token" and "repos" keys

    Raises:
        ValueError: If code is invalid
    """
    if "-" not in code:
        raise ValueError("Invalid config code: expected PREFIX-base64data format")

    _, b64 = code.split("-", 1)
    try:
        data = json.loads(base64.b64decode(b64))
    except Exception as e:
        raise ValueError(f"Invalid config code: {e}") from e

    if "token" not in data or "repos" not in data:
        raise ValueError("Invalid config code: missing token or repos")

    return data


def load_config() -> dict | None:
    """Load config from disk.

    Returns:
        Config dict or None if not configured.
        For v2 format, contains "token" and "repos" keys.
        Converts stored "tools" to internal Tool objects.
    """
    path = get_config_path()
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text())
        # If we have repos but no tools, we need to fetch manifests
        # For now, return the raw config - tray.py will handle conversion
        return data
    except (json.JSONDecodeError, OSError):
        return None


def save_config(config: dict) -> None:
    """Save config to disk.

    Args:
        config: Dict with "token" and "repos" keys (v2 format)
    """
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2))


def config_exists() -> bool:
    """Check if config file exists."""
    return get_config_path().exists()
