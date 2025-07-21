"""Data models for Google Drive plugin."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AuthType(Enum):
    """Authentication types for Google Drive."""
    OAUTH = "oauth"
    SERVICE_ACCOUNT = "service_account"


class GoogleDriveSource(BaseModel):
    """Model for a Google Drive source configuration."""
    id: str = Field(..., description="Unique identifier for this source config")
    drive_id: str = Field(default="root", description="Drive ID or 'root' for My Drive")
    folder_id: Optional[str] = Field(default=None, description="Specific folder ID to ingest from")
    file_types: List[str] = Field(
        default=["document", "spreadsheet", "presentation", "pdf"],
        description="Types of files to include"
    )
    exclude_patterns: Optional[List[str]] = Field(
        default=None,
        description="File name patterns to exclude (glob patterns)"
    )
    include_shared: bool = Field(default=True, description="Include files shared with the user")
    include_trashed: bool = Field(default=False, description="Include trashed files")
    recursive: bool = Field(default=True, description="Recursively traverse subfolders (only applies when folder_id is set)")
    last_synced: Optional[datetime] = Field(default=None, description="Last sync timestamp")
    sync_mode: Literal["full", "incremental"] = Field(
        default="full",
        description="Sync mode: 'full' or 'incremental'"
    )
    page_token: Optional[str] = Field(
        default=None,
        description="Page token for tracking changes in incremental sync"
    )

    def get_display_name(self) -> str:
        """Get a display name for this source."""
        if self.folder_id:
            return f"Folder: {self.folder_id}"
        elif self.drive_id == "root":
            return "My Drive"
        else:
            return f"Drive: {self.drive_id}"


class GoogleDriveFile(BaseModel):
    """Model for Google Drive file metadata."""
    id: str = Field(..., description="Google Drive file ID")
    name: str = Field(..., description="File name")
    mime_type: str = Field(..., description="MIME type of the file")
    size: Optional[int] = Field(default=None, description="File size in bytes")
    created_time: datetime = Field(..., description="File creation timestamp")
    modified_time: datetime = Field(..., description="Last modified timestamp")
    parent_ids: List[str] = Field(default_factory=list, description="Parent folder IDs")
    md5_checksum: Optional[str] = Field(default=None, description="MD5 checksum for change detection")
    web_view_link: Optional[str] = Field(default=None, description="Web view link")
    owners: List[str] = Field(default_factory=list, description="List of owner emails")
    shared: bool = Field(default=False, description="Whether the file is shared")


class GoogleDriveConfig(BaseModel):
    """Configuration for Google Drive plugin."""
    enabled: bool = Field(default=False, description="Whether the plugin is enabled")
    auth_type: Literal["oauth", "service_account"] = Field(
        default="oauth",
        description="Authentication type"
    )
    config: Dict[str, Any] = Field(default_factory=dict)

    @property
    def sources(self) -> List[GoogleDriveSource]:
        """Get list of source configurations."""
        source_configs = self.config.get("sources", [])
        return [GoogleDriveSource(**source) for source in source_configs]

    @property
    def oauth_config(self) -> Optional[Dict[str, str]]:
        """Get OAuth configuration."""
        if self.auth_type == "oauth":
            return self.config.get("oauth_config", {})
        return None

    @property
    def service_account_config(self) -> Optional[Dict[str, str]]:
        """Get service account configuration."""
        if self.auth_type == "service_account":
            return self.config.get("service_account_config", {})
        return None


class GoogleDriveIngestionJob(BaseModel):
    """Model for tracking Google Drive ingestion job."""
    source_id: str
    drive_id: str
    folder_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    files_processed: int = 0
    files_failed: int = 0
    total_files: int = 0
    status: str = "running"
    error_message: Optional[str] = None 