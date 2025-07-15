"""Plugin-related schemas for API."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PluginConfigRequest(BaseModel):
    """Request model for updating plugin configuration."""
    enabled: bool = Field(..., description="Whether the plugin is enabled")
    config: Dict[str, Any] = Field(..., description="Plugin-specific configuration")


class PluginConfigResponse(BaseModel):
    """Response model for plugin configuration."""
    plugin_name: str
    enabled: bool
    config: Dict[str, Any]


class PluginInfoResponse(BaseModel):
    """Response model for plugin information."""
    name: str
    display_name: str
    description: str
    version: str
    author: str
    capabilities: List[str]
    enabled: bool
    initialized: bool
    total_sources: Optional[int] = 0


class PluginListResponse(BaseModel):
    """Response model for listing plugins."""
    plugins: List[PluginInfoResponse]


class IngestionRequest(BaseModel):
    """Request model for triggering ingestion."""
    source_id: str = Field(..., description="Source identifier")
    full_sync: bool = Field(default=True, description="Whether to perform full sync")


class IngestionResponse(BaseModel):
    """Response model for ingestion trigger."""
    job_id: str
    plugin_name: str
    source_id: str
    sync_type: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    id: str
    plugin_name: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_documents: int = 0
    processed_documents: int = 0
    failed_documents: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SourceInfo(BaseModel):
    """Model for source information."""
    id: str
    name: str
    type: str
    config: Dict[str, Any]
    last_synced: Optional[datetime] = None
    sync_mode: str
    enabled: bool


class SourceListResponse(BaseModel):
    """Response model for listing sources."""
    sources: List[SourceInfo]


class GlobalSettingsRequest(BaseModel):
    """Request model for updating global settings."""
    chunk_size: int = Field(default=1024, ge=128, le=4096)
    chunk_overlap: int = Field(default=200, ge=0, le=1024)
    batch_size: int = Field(default=100, ge=1, le=1000)
    auto_sync: bool = Field(default=False)
    sync_interval_hours: int = Field(default=24, ge=1, le=168)


class GlobalSettingsResponse(BaseModel):
    """Response model for global settings."""
    chunk_size: int
    chunk_overlap: int
    batch_size: int
    auto_sync: bool
    sync_interval_hours: int


class ConfigurationResponse(BaseModel):
    """Response model for full configuration."""
    version: str
    plugins: Dict[str, PluginConfigResponse]
    global_settings: GlobalSettingsResponse 