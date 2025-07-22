"""Data models for GitHub plugin."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class GitHubRepository(BaseModel):
    """Model for a GitHub repository configuration."""
    id: str = Field(..., description="Unique identifier for this repository config")
    owner: str = Field(..., description="Repository owner (user or organization)")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(default="main", description="Branch to ingest from")
    paths: Optional[List[str]] = Field(default=None, description="Specific paths to include")
    exclude_patterns: Optional[List[str]] = Field(default=None, description="File patterns to exclude")
    last_synced: Optional[datetime] = Field(default=None, description="Last sync timestamp")
    sync_mode: str = Field(default="full", description="Sync mode: 'full' or 'incremental'")
    
    def get_full_name(self) -> str:
        """Get the full repository name."""
        return f"{self.owner}/{self.repo}"


class GitHubConfig(BaseModel):
    """Configuration for GitHub plugin."""
    enabled: bool = Field(default=False, description="Whether the plugin is enabled")
    config: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def repositories(self) -> List[GitHubRepository]:
        """Get list of repository configurations."""
        repo_configs = self.config.get("repositories", [])
        return [GitHubRepository(**repo) for repo in repo_configs]
    
    @property
    def github_token(self) -> Optional[str]:
        """Get GitHub token from config."""
        return self.config.get("github_token")

