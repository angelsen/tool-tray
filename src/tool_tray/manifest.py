import tomllib
from dataclasses import dataclass

import httpx


@dataclass
class Manifest:
    """Tool manifest from tooltray.toml."""

    name: str
    type: str  # "uv" | "git" | "curl"
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


@dataclass
class RepoManifest:
    """A repo with its resolved manifest."""

    repo: str  # "org/repo"
    manifest: Manifest | None = None
    error: str | None = None

    @property
    def name(self) -> str:
        """Get display name from manifest or repo name."""
        if self.manifest:
            return self.manifest.name
        return self.repo.split("/")[-1]

    @property
    def is_valid(self) -> bool:
        """Check if repo has a valid manifest."""
        return self.manifest is not None


def fetch_manifest(repo: str, token: str) -> Manifest | None:
    """Fetch tooltray.toml from GitHub repo.

    Args:
        repo: Repository in "org/repo" format
        token: GitHub PAT for authentication

    Returns:
        Manifest if found and valid, None otherwise
    """
    url = f"https://api.github.com/repos/{repo}/contents/tooltray.toml"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.raw+json",
    }
    try:
        resp = httpx.get(url, headers=headers, timeout=10)
        if resp.status_code == 404:
            return None  # No manifest in repo
        resp.raise_for_status()
        data = tomllib.loads(resp.text)
        return Manifest.from_dict(data)
    except (httpx.HTTPError, tomllib.TOMLDecodeError, KeyError):
        return None


def fetch_all_manifests(repos: list[str], token: str) -> list[RepoManifest]:
    """Fetch manifests for all repos.

    Args:
        repos: List of repos in "org/repo" format
        token: GitHub PAT for authentication

    Returns:
        List of RepoManifest objects (some may have no manifest)
    """
    results = []
    for repo in repos:
        manifest = fetch_manifest(repo, token)
        if manifest:
            results.append(RepoManifest(repo=repo, manifest=manifest))
        else:
            results.append(RepoManifest(repo=repo, error="No tooltray.toml found"))
    return results
