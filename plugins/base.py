"""Base plugin interface for ingestion plugins."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class IngestionStatus(str, Enum):
    """Status of an ingestion job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IngestionJob(BaseModel):
    """Model for tracking ingestion jobs."""
    id: str
    plugin_name: str
    status: IngestionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_documents: int = 0
    processed_documents: int = 0
    failed_documents: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class IngestionPlugin(ABC):
    """Abstract base class for ingestion plugins."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self._jobs: Dict[str, IngestionJob] = {}
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the plugin configuration.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        pass
    
    @abstractmethod
    async def ingest(self, source_id: str, full_sync: bool = True) -> str:
        """Perform ingestion from the configured source.
        
        Args:
            source_id: Identifier for the specific source to ingest
            full_sync: If True, perform full sync. If False, incremental.
            
        Returns:
            Job ID for tracking the ingestion progress.
        """
        pass
    
    @abstractmethod
    async def get_sources(self) -> List[Dict[str, Any]]:
        """Get list of configured sources for this plugin.
        
        Returns:
            List of source configurations with their metadata.
        """
        pass
    
    def get_job_status(self, job_id: str) -> Optional[IngestionJob]:
        """Get the status of an ingestion job.
        
        Args:
            job_id: The job identifier
            
        Returns:
            IngestionJob object or None if not found.
        """
        return self._jobs.get(job_id)
    
    def list_jobs(self) -> List[IngestionJob]:
        """List all ingestion jobs for this plugin.
        
        Returns:
            List of IngestionJob objects.
        """
        return list(self._jobs.values())
    
    def create_job(self, source_id: str, metadata: Optional[Dict[str, Any]] = None) -> IngestionJob:
        """Create a new ingestion job.
        
        Args:
            source_id: The source identifier
            metadata: Optional metadata for the job
            
        Returns:
            Created IngestionJob object.
        """
        import uuid
        job_id = str(uuid.uuid4())
        job = IngestionJob(
            id=job_id,
            plugin_name=self.name,
            status=IngestionStatus.PENDING,
            metadata=metadata or {}
        )
        self._jobs[job_id] = job
        return job
    
    def update_job(self, job_id: str, **kwargs) -> Optional[IngestionJob]:
        """Update an existing job.
        
        Args:
            job_id: The job identifier
            **kwargs: Fields to update
            
        Returns:
            Updated IngestionJob or None if not found.
        """
        job = self._jobs.get(job_id)
        if job:
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
        return job
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about the plugin.
        
        Returns:
            Dictionary with plugin information.
        """
        pass 