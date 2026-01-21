import re
import subprocess

import httpx

from tool_tray.manifest import Manifest


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


def get_remote_version(repo: str, token: str) -> str | None:
    """Fetch version from pyproject.toml via GitHub API."""
    url = f"https://api.github.com/repos/{repo}/contents/pyproject.toml"
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


def _install_url(repo: str, token: str) -> str:
    """Get the git URL for uv tool install."""
    return f"git+https://oauth2:{token}@github.com/{repo}"


def install_tool(repo: str, manifest: Manifest, token: str) -> bool:
    """Install or update tool based on manifest type."""
    if manifest.type == "uv":
        return _install_uv_tool(repo, token)
    elif manifest.type == "git":
        return _install_git_tool(repo, manifest, token)
    elif manifest.type == "curl":
        return _install_curl_tool(repo, manifest, token)
    return False


def _install_uv_tool(repo: str, token: str) -> bool:
    """Install or update tool via uv tool install --force."""
    try:
        subprocess.run(
            ["uv", "tool", "install", _install_url(repo, token), "--force"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _install_git_tool(repo: str, manifest: Manifest, token: str) -> bool:
    """Install tool via git clone + optional build command."""
    from pathlib import Path

    clone_url = f"https://oauth2:{token}@github.com/{repo}"
    install_dir = Path.home() / ".local/share/tooltray" / repo.split("/")[-1]

    try:
        # Remove existing if present
        if install_dir.exists():
            import shutil

            shutil.rmtree(install_dir)

        install_dir.parent.mkdir(parents=True, exist_ok=True)

        # Clone repo
        subprocess.run(
            ["git", "clone", "--depth=1", clone_url, str(install_dir)],
            check=True,
            capture_output=True,
        )

        # Run build command if specified
        if manifest.build:
            subprocess.run(
                manifest.build,
                shell=True,
                cwd=install_dir,
                check=True,
                capture_output=True,
            )

        return True
    except subprocess.CalledProcessError:
        return False


def _install_curl_tool(repo: str, manifest: Manifest, token: str) -> bool:
    """Install tool by downloading release archive."""
    # For curl type, we'd download from releases
    # This is a placeholder for future implementation
    return False
