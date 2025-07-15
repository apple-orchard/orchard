"""GitHub ingestion plugin."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from plugins.base import IngestionPlugin, IngestionStatus, IngestionJob
from plugins.github.models import GitHubConfig, GitHubRepository
from plugins.github.reader import GitHubReader
from plugins.llamaindex.converters import convert_llama_doc_to_chunks, convert_github_metadata
from app.utils.database import chroma_db
from app.core.config import settings


class GithubIngestionPlugin(IngestionPlugin):
    """GitHub repository ingestion plugin."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._reader: Optional[GitHubReader] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    def validate_config(self) -> bool:
        """Validate the plugin configuration."""
        try:
            config = GitHubConfig(**self.config)
            return config.enabled and bool(config.github_token)
        except Exception:
            return False
    
    def _get_reader(self) -> GitHubReader:
        """Get or create the GitHub reader instance."""
        if self._reader is None:
            config = GitHubConfig(**self.config)
            self._reader = GitHubReader(github_token=config.github_token)
        return self._reader
    
    async def get_sources(self) -> List[Dict[str, Any]]:
        """Get list of configured GitHub repositories."""
        config = GitHubConfig(**self.config)
        return [
            {
                "id": repo.id,
                "name": repo.get_full_name(),
                "type": "github_repository",
                "enabled": True,
                "config": {
                    "owner": repo.owner,
                    "repo": repo.repo,
                    "branch": repo.branch,
                    "paths": repo.paths,
                    "exclude_patterns": repo.exclude_patterns
                },
                "last_synced": repo.last_synced,
                "sync_mode": repo.sync_mode
            }
            for repo in config.repositories
        ]
    
    async def ingest(self, source_id: str, full_sync: bool = True) -> str:
        """Perform ingestion from a GitHub repository.
        
        Args:
            source_id: Repository ID from configuration
            full_sync: If True, perform full sync. If False, incremental.
            
        Returns:
            Job ID for tracking the ingestion progress.
        """
        # Find the repository configuration
        config = GitHubConfig(**self.config)
        repo = None
        for r in config.repositories:
            if r.id == source_id:
                repo = r
                break
        
        if not repo:
            raise ValueError(f"Repository with ID {source_id} not found")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = IngestionJob(
            id=job_id,
            plugin_name=self.name,
            status=IngestionStatus.PENDING
        )
        self._jobs[job_id] = job
        
        # Start ingestion in background
        asyncio.create_task(self._perform_ingestion(job_id, repo, full_sync))
        
        return job.id
    
    async def _perform_ingestion(self, job_id: str, repo: GitHubRepository, full_sync: bool) -> None:
        """Perform the actual ingestion work.
        
        Args:
            job_id: Job ID to update
            repo: Repository configuration
            full_sync: Whether to perform full sync
        """
        try:
            # Update job status
            self.update_job(
                job_id, 
                status=IngestionStatus.RUNNING, 
                started_at=datetime.now(),
                metadata={
                    "repository": repo.get_full_name(),
                    "branch": repo.branch,
                    "sync_type": "full" if full_sync else "incremental",
                    "current_action": "connecting"
                }
            )
            
            reader = self._get_reader()
            
            if full_sync:
                # Update status: fetching
                self.update_job(job_id, metadata={
                    **self._jobs[job_id].metadata,
                    "current_action": "fetching",
                    "details": f"Fetching files from {repo.get_full_name()}"
                })
                
                # Full sync - read all documents
                # Run in thread pool to avoid event loop conflicts
                documents = await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    reader.read_repository,
                    repo.owner,
                    repo.repo,
                    repo.branch,
                    repo.paths,
                    repo.exclude_patterns
                )
                
                # Update with document count
                self.update_job(job_id, total_documents=len(documents))
                
                # Delete existing chunks for this repository
                self._delete_existing_chunks(repo.get_full_name())
            else:
                # Incremental sync - read only changed documents
                cache_file = f".github_cache/{repo.id}.json"
                result = await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    reader.read_incremental,
                    repo.owner,
                    repo.repo,
                    repo.branch,
                    cache_file,
                    repo.paths,
                    repo.exclude_patterns
                )
                documents = result["documents"]
                
                # Delete chunks for modified files
                for file_path in result["changes"]["modified"]:
                    self._delete_file_chunks(repo.get_full_name(), file_path)
            
            # Enrich metadata
            reader.enrich_metadata(documents, repo.owner, repo.repo, repo.branch)
            
            # Update status: chunking
            self.update_job(job_id, metadata={
                **self._jobs[job_id].metadata,
                "current_action": "chunking",
                "details": f"Creating chunks from {len(documents)} documents"
            })
            
            # Convert to chunks
            source_metadata = convert_github_metadata({
                "owner": repo.owner,
                "repo": repo.repo,
                "branch": repo.branch
            })
            
            chunks = convert_llama_doc_to_chunks(documents, source_metadata)
            
            # Update status: storing
            self.update_job(job_id, 
                total_documents=len(chunks),  # Update total to chunks count
                metadata={
                    **self._jobs[job_id].metadata,
                    "current_action": "storing",
                    "details": f"Storing {len(chunks)} chunks in vector database"
                }
            )
            
            # Store in vector database
            chunk_ids = [f"{repo.get_full_name()}_{i}" for i in range(len(chunks))]
            
            # Add chunks in batches
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i+batch_size]
                batch_ids = chunk_ids[i:i+batch_size]
                
                texts = [chunk["content"] for chunk in batch_chunks]
                metadatas = [chunk["metadata"] for chunk in batch_chunks]
                
                # Add to ChromaDB
                chroma_db.add_documents(
                    chunks=texts,
                    metadatas=metadatas
                )
                
                # Update progress
                self.update_job(job_id, processed_documents=min(i + batch_size, len(chunks)))
            
            # Mark job as completed
            self.update_job(
                job_id,
                status=IngestionStatus.COMPLETED,
                completed_at=datetime.now(),
                processed_documents=len(chunks)
            )
            
        except Exception as e:
            import traceback
            # Get detailed error information
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "repository": repo.get_full_name(),
                "branch": repo.branch
            }
            
            # Log the error
            print(f"ERROR: Ingestion failed for {repo.get_full_name()}")
            print(f"Error Type: {error_details['error_type']}")
            print(f"Error Message: {error_details['error_message']}")
            print(f"Branch: {repo.branch}")
            print(f"Traceback:\n{error_details['traceback']}")
            
            # Mark job as failed with detailed error
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
    
    def _delete_existing_chunks(self, repository: str) -> None:
        """Delete all existing chunks for a repository.
        
        Args:
            repository: Full repository name (owner/repo)
        """
        # This is a simplified version - actual implementation would
        # need to query and delete based on metadata
        # ChromaDB doesn't have a direct way to delete by metadata filter
        # You might need to implement a custom solution based on your needs
        pass
    
    def _delete_file_chunks(self, repository: str, file_path: str) -> None:
        """Delete chunks for a specific file.
        
        Args:
            repository: Full repository name (owner/repo)
            file_path: Path of the file to delete chunks for
        """
        # Similar to above - would need custom implementation
        pass
    
    def update_job(self, job_id: str, **kwargs) -> None:
        """Update job information.
        
        Args:
            job_id: Job ID
            **kwargs: Fields to update
        """
        if job_id in self._jobs:
            job = self._jobs[job_id]
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about the plugin."""
        config = GitHubConfig(**self.config)
        return {
            "name": self.name,
            "display_name": "GitHub Repository Ingestion",
            "description": "Ingest code and documentation from GitHub repositories",
            "version": "1.0.0",
            "author": "Orchard RAG",
            "capabilities": [
                "full_sync",
                "incremental_sync", 
                "path_filtering",
                "exclude_patterns",
                "branch_selection"
            ],
            "enabled": config.enabled,
            "initialized": True,
            "total_sources": len(config.repositories) if config.enabled else 0
        }
    
    def __del__(self):
        """Cleanup thread pool executor."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False) 