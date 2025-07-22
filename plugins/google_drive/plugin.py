"""Google Drive ingestion plugin."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import traceback
import logging

from plugins.base import IngestionPlugin, IngestionStatus, IngestionJob
from plugins.google_drive.models import GoogleDriveConfig, GoogleDriveSource
from plugins.google_drive.reader import GoogleDriveReaderWrapper
from plugins.llamaindex.converters import convert_llama_doc_to_chunks
from app.utils.database import chroma_db
from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleDriveIngestionPlugin(IngestionPlugin):
    """Google Drive ingestion plugin."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._reader: Optional[GoogleDriveReaderWrapper] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        
    def validate_config(self) -> bool:
        """Validate the plugin configuration."""
        try:
            config = GoogleDriveConfig(**self.config)
            if not config.enabled:
                return False
                
            # Check auth configuration
            if config.auth_type == "oauth":
                oauth_config = config.oauth_config
                return bool(
                    oauth_config and 
                    oauth_config.get("client_id") and
                    oauth_config.get("client_secret") and
                    oauth_config.get("refresh_token")
                )
            elif config.auth_type == "service_account":
                sa_config = config.service_account_config
                return bool(sa_config and sa_config.get("key_file"))
            
            return False
        except Exception:
            return False
    
    def _get_reader(self) -> GoogleDriveReaderWrapper:
        """Get or create the Google Drive reader instance."""
        if self._reader is None:
            config = GoogleDriveConfig(**self.config)
            
            if config.auth_type == "oauth":
                auth_config = config.oauth_config
            else:
                auth_config = config.service_account_config
            
            self._reader = GoogleDriveReaderWrapper(
                auth_config=auth_config,
                auth_type=config.auth_type
            )
        return self._reader
    
    async def get_sources(self) -> List[Dict[str, Any]]:
        """Get list of configured Google Drive sources."""
        config = GoogleDriveConfig(**self.config)
        return [
            {
                "id": source.id,
                "name": source.get_display_name(),
                "type": "google_drive",
                "enabled": True,
                "config": {
                    "drive_id": source.drive_id,
                    "folder_id": source.folder_id,
                    "file_types": source.file_types,
                    "exclude_patterns": source.exclude_patterns,
                    "include_shared": source.include_shared,
                    "include_trashed": source.include_trashed
                },
                "last_synced": source.last_synced.isoformat() if source.last_synced else None,
                "sync_mode": source.sync_mode
            }
            for source in config.sources
        ]
    
    async def ingest(self, source_id: str, full_sync: bool = True) -> str:
        """Perform ingestion from a Google Drive source.
        
        Args:
            source_id: Source ID from configuration
            full_sync: If True, perform full sync. If False, incremental.
            
        Returns:
            Job ID for tracking the ingestion progress.
        """
        # Find the source configuration
        config = GoogleDriveConfig(**self.config)
        source = None
        for s in config.sources:
            if s.id == source_id:
                source = s
                break
        
        if not source:
            raise ValueError(f"Source with ID {source_id} not found")
        
        # Override sync mode if specified
        if not full_sync and source.sync_mode == "incremental":
            full_sync = False
        else:
            full_sync = True
        
        # Create job
        job_id = str(uuid.uuid4())
        job = IngestionJob(
            id=job_id,
            plugin_name=self.name,
            status=IngestionStatus.PENDING
        )
        self._jobs[job_id] = job
        
        # Start ingestion in background
        asyncio.create_task(self._perform_ingestion(job_id, source, full_sync))
        
        return job.id
    
    async def _perform_ingestion(self, job_id: str, source: GoogleDriveSource, full_sync: bool) -> None:
        """Perform the actual ingestion work.
        
        Args:
            job_id: Job ID to update
            source: Google Drive source configuration
            full_sync: Whether to perform full sync
        """
        try:
            # Update job status
            self.update_job(
                job_id,
                status=IngestionStatus.RUNNING,
                started_at=datetime.now(),
                metadata={
                    "source": source.get_display_name(),
                    "drive_id": source.drive_id,
                    "folder_id": source.folder_id,
                    "sync_type": "full" if full_sync else "incremental",
                    "current_action": "connecting"
                }
            )
            
            reader = self._get_reader()
            
            # Test connection
            self.update_job(job_id, metadata={
                **self._jobs[job_id].metadata,
                "current_action": "testing_connection"
            })
            
            if not reader.test_connection():
                raise Exception("Failed to connect to Google Drive")
            
            # Update status: fetching
            self.update_job(job_id, metadata={
                **self._jobs[job_id].metadata,
                "current_action": "fetching",
                "details": f"Reading files from {source.get_display_name()}"
            })
            
            # Create progress callback
            def update_file_progress(processed: int, total: int):
                self.update_job(
                    job_id,
                    processed_documents=processed,
                    total_documents=total,
                    metadata={
                        **self._jobs[job_id].metadata,
                        "current_action": "fetching",
                        "details": f"Loading file {processed}/{total}"
                    }
                )
            
            # Read files with progress updates
            documents, sync_metadata = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                reader.read_files,
                source,
                full_sync,
                update_file_progress
            )
            
            # Update with document count
            self.update_job(job_id, total_documents=len(documents))
            
            # Convert to chunks
            self.update_job(job_id, metadata={
                **self._jobs[job_id].metadata,
                "current_action": "chunking",
                "details": f"Creating chunks from {len(documents)} documents (using smart chunking)"
            })
            
            # Convert Google Drive metadata format
            source_metadata = {
                "source": "google_drive",
                "drive_id": source.drive_id,
                "folder_id": source.folder_id,
                "source_id": source.id
            }
            
            logger.info("Converting %s documents to chunks...", len(documents))
            chunks = convert_llama_doc_to_chunks(documents, source_metadata)
            logger.info("Created %s chunks from %s documents", len(chunks), len(documents))
            
            # Update status with chunking results
            self.update_job(job_id, metadata={
                **self._jobs[job_id].metadata,
                "details": f"Created {len(chunks)} chunks from {len(documents)} documents"
            })
            
            # Update status: storing
            self.update_job(job_id,
                processed_documents=0,  # Reset processed count for chunk storage
                total_documents=len(chunks),  # Update total to chunks count
                metadata={
                    **self._jobs[job_id].metadata,
                    "current_action": "storing",
                    "details": f"Storing {len(chunks)} chunks in vector database"
                }
            )
            
            # Store in vector database
            if full_sync and source.folder_id:
                # Delete existing chunks for this source
                # Note: This would need custom implementation in ChromaDB
                pass
            
            # Add chunks in batches
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i+batch_size]
                
                texts = [chunk["content"] for chunk in batch_chunks]
                metadatas = [chunk["metadata"] for chunk in batch_chunks]
                
                # Add to ChromaDB
                chroma_db.add_documents(
                    chunks=texts,
                    metadatas=metadatas
                )
                
                # Update progress
                self.update_job(job_id, processed_documents=min(i + batch_size, len(chunks)))
            
            # Update source configuration with sync metadata
            if "page_token" in sync_metadata:
                source.page_token = sync_metadata["page_token"]
            source.last_synced = datetime.now()
            
            # Mark job as completed
            self.update_job(
                job_id,
                status=IngestionStatus.COMPLETED,
                completed_at=datetime.now(),
                processed_documents=len(chunks),
                metadata={
                    **self._jobs[job_id].metadata,
                    "sync_metadata": sync_metadata
                }
            )
            
        except Exception as e:
            # Get detailed error information
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "source": source.get_display_name(),
                "drive_id": source.drive_id,
                "folder_id": source.folder_id
            }
            
            # Log the error
            logger.error(
                "Ingestion failed for %s\nType: %s\nMessage: %s\nDrive ID: %s\nFolder ID: %s\nTraceback:\n%s",
                source.get_display_name(),
                error_details["error_type"],
                error_details["error_message"],
                source.drive_id,
                source.folder_id or "N/A",
                error_details["traceback"],
            )
            
            # Mark job as failed
            self.update_job(
                job_id,
                status=IngestionStatus.FAILED,
                completed_at=datetime.now(),
                error_message=str(e),
                metadata={
                    **self._jobs[job_id].metadata,
                    "error_details": error_details
                }
            )
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about the plugin."""
        config = GoogleDriveConfig(**self.config)
        return {
            "name": self.name,
            "display_name": "Google Drive Ingestion",
            "description": "Ingest documents from Google Drive including Google Docs, Sheets, and other file types",
            "version": "1.0.0",
            "author": "Orchard RAG",
            "capabilities": [
                "full_sync",
                "incremental_sync",
                "folder_filtering",
                "file_type_filtering",
                "exclude_patterns",
                "oauth_auth",
                "service_account_auth"
            ],
            "enabled": config.enabled,
            "auth_type": config.auth_type,
            "initialized": self._reader is not None,
            "total_sources": len(config.sources) if config.enabled else 0
        }
    
    def __del__(self):
        """Cleanup thread pool executor."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False) 