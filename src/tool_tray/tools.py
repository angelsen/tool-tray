from dataclasses import dataclass


@dataclass
class Tool:
    """A tool that can be installed via uv."""

    name: str
    repo: str  # "Org/RepoName"

    def install_url(self, token: str) -> str:
        """Get the git URL for uv tool install."""
        return f"git+https://oauth2:{token}@github.com/{self.repo}"

    @classmethod
    def from_dict(cls, data: dict) -> "Tool":
        """Create Tool from config dict."""
        return cls(name=data["name"], repo=data["repo"])

    def to_dict(self) -> dict:
        """Convert to config dict."""
        return {"name": self.name, "repo": self.repo}
