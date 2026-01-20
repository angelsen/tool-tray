import re
import subprocess

import httpx

from tool_tray.tools import Tool


def get_installed_version(tool_name: str) -> str | None:
    """Get installed version from uv tool list."""
    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith(tool_name):
                match = re.search(r"v?(\d+\.\d+\.\d+)", line)
                if match:
                    return match.group(1)
        return None
    except subprocess.CalledProcessError:
        return None


def get_remote_version(tool: Tool, token: str) -> str | None:
    """Fetch version from pyproject.toml via GitHub API."""
    url = f"https://api.github.com/repos/{tool.repo}/contents/pyproject.toml"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.raw+json",
    }
    try:
        resp = httpx.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        content = resp.text
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        return None
    except httpx.HTTPError:
        return None


def install_tool(tool: Tool, token: str) -> bool:
    """Install or update tool via uv tool install --force."""
    try:
        subprocess.run(
            ["uv", "tool", "install", tool.install_url(token), "--force"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False
