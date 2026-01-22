import tomllib
from dataclasses import dataclass

import httpx


@dataclass
class Manifest:
    """Tool manifest from tooltray.toml."""

    name: str
    type: str  # "uv" | "git"
    launch: str | None = None
    build: str | None = None
    desktop_icon: bool = False
    icon: str | None = None
    autostart: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "Manifest":
        """Create Manifest from parsed TOML dict."""
        return cls(
            name=data["name"],
            type=data["type"],
            launch=data.get("launch"),
            build=data.get("build"),
            desktop_icon=data.get("desktop_icon", False),
            icon=data.get("icon"),
            autostart=data.get("autostart", False),
        )


def fetch_manifest(repo: str, token: str) -> Manifest | None:
    """Fetch tooltray.toml from GitHub repo."""
    from tool_tray.logging import log_debug, log_error

    url = f"https://api.github.com/repos/{repo}/contents/tooltray.toml"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.raw+json",
    }
    log_debug(f"Fetching manifest: {repo}")
    try:
        resp = httpx.get(url, headers=headers, timeout=10)
        if resp.status_code == 404:
            log_debug(f"No manifest found: {repo}")
            return None
        resp.raise_for_status()
        data = tomllib.loads(resp.text)
        manifest = Manifest.from_dict(data)
        log_debug(f"Manifest loaded: {repo} -> {manifest.name} ({manifest.type})")
        return manifest
    except httpx.HTTPError as e:
        log_error(f"HTTP error fetching manifest: {repo}", e)
        return None
    except tomllib.TOMLDecodeError as e:
        log_error(f"Invalid TOML in manifest: {repo}", e)
        return None
    except KeyError as e:
        log_error(f"Missing required field in manifest: {repo}", e)
        return None
