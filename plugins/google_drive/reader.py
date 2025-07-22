"""Google Drive reader implementation."""

import os
import json
import fnmatch
import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime
from pathlib import Path

from llama_index.readers.google import GoogleDriveReader
from llama_index.core.schema import Document as LlamaDocument

from plugins.google_drive.models import GoogleDriveSource

logger = logging.getLogger(__name__)


class GoogleDriveReaderWrapper:
    """Wrapper around LlamaIndex Google Drive reader with additional functionality."""
    
    # MIME type mappings for Google native formats
    GOOGLE_MIME_TYPES = {
        "application/vnd.google-apps.document": "document",
        "application/vnd.google-apps.spreadsheet": "spreadsheet", 
        "application/vnd.google-apps.presentation": "presentation",
        "application/vnd.google-apps.drawing": "drawing",
        "application/vnd.google-apps.form": "form"
    }
    
    # Standard file types we support
    STANDARD_MIME_TYPES = {
        "application/pdf": "pdf",
        "text/plain": "text",
        "text/csv": "csv",
        "text/markdown": "markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx"
    }
    
    def __init__(self, auth_config: Dict[str, Any], auth_type: str = "oauth"):
        """Initialize Google Drive reader.
        
        Args:
            auth_config: Authentication configuration
            auth_type: Type of authentication ("oauth" or "service_account")
        """
        self.auth_type = auth_type
        self.auth_config = auth_config
        self._reader = None
        self._setup_reader()
        
    def _setup_reader(self):
        """Set up the Google Drive reader based on authentication type."""
        if self.auth_type == "oauth":
            # OAuth authentication
            self._reader = GoogleDriveReader(
                client_id=self.auth_config.get("client_id"),
                client_secret=self.auth_config.get("client_secret"),
                refresh_token=self.auth_config.get("refresh_token")
            )
        else:
            # Service account authentication
            key_file = os.path.expandvars(self.auth_config.get("key_file", ""))
            # Load the service account key JSON file
            with open(key_file, 'r') as f:
                service_account_key = json.load(f)
            
            self._reader = GoogleDriveReader(
                service_account_key=service_account_key,
                delegated_user=self.auth_config.get("delegated_user")
            )
    
    def read_files(
        self,
        source: GoogleDriveSource,
        full_sync: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[List[LlamaDocument], Dict[str, Any]]:
        """Read files from Google Drive.
        
        Args:
            source: Google Drive source configuration
            full_sync: Whether to perform full sync or incremental
            progress_callback: Optional callback for progress updates (processed, total)
            
        Returns:
            Tuple of (documents, sync_metadata)
        """
        if full_sync:
            return self._full_sync(source, progress_callback)
        else:
            return self._incremental_sync(source, progress_callback)
    
    def _full_sync(self, source: GoogleDriveSource, progress_callback: Optional[Callable[[int, int], None]] = None) -> Tuple[List[LlamaDocument], Dict[str, Any]]:
        """Perform full sync of Google Drive files."""
        documents = []
        
        # For folder-based sources with recursive enabled, use recursive traversal
        if source.folder_id and source.recursive:
            logger.info("Starting recursive traversal of folder %s...", source.folder_id)
            
            # Create a Google Drive service client
            from googleapiclient.discovery import build
            from google.oauth2 import service_account
            import json
            
            if self.auth_type == "service_account":
                # Create service from service account
                key_file = self.auth_config.get("key_file") or self.auth_config.get("service_account_file")
                with open(key_file, 'r') as f:
                    service_account_key = json.load(f)
                
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_key,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                service = build('drive', 'v3', credentials=credentials)
            else:
                # For OAuth, we'd need to handle it differently
                raise NotImplementedError("Recursive traversal not yet implemented for OAuth authentication")
            
            # Get all files recursively
            all_files = self._get_folder_contents_recursive(source.folder_id, source, service)
            logger.info("Found %s files in folder and subfolders", len(all_files))
            
            # Update initial progress if callback provided
            if progress_callback:
                progress_callback(0, len(all_files))
            
            # Process each file
            for i, file_metadata in enumerate(all_files):
                try:
                    # Load the file using the reader
                    file_docs = self._reader.load_data(file_ids=[file_metadata['id']])
                    if file_docs:
                        # Add folder path to document metadata
                        for doc in file_docs:
                            if doc.metadata:
                                doc.metadata['folder_path'] = file_metadata.get('folder_path', '')
                        documents.extend(file_docs)
                    
                    # Update progress
                    if progress_callback:
                        progress_callback(i + 1, len(all_files))
                        
                except Exception as e:
                    logger.warning("Error loading file %s: %s", file_metadata.get('name', 'Unknown'), e)
                    # Still update progress even on error
                    if progress_callback:
                        progress_callback(i + 1, len(all_files))
            
            return documents, {"files_processed": len(all_files)}
        
        # For non-folder sources or non-recursive folder sources, use the original query-based approach
        # Build query for Google Drive API
        query_parts = []
        
        # Add folder filter if specified and not recursive
        if source.folder_id and not source.recursive:
            query_parts.append(f"'{source.folder_id}' in parents")
        
        # Add file type filters
        mime_conditions = []
        for file_type in source.file_types:
            if file_type == "document":
                mime_conditions.append("mimeType='application/vnd.google-apps.document'")
            elif file_type == "spreadsheet":
                mime_conditions.append("mimeType='application/vnd.google-apps.spreadsheet'")
            elif file_type == "presentation":
                mime_conditions.append("mimeType='application/vnd.google-apps.presentation'")
            elif file_type == "pdf":
                mime_conditions.append("mimeType='application/pdf'")
        
        if mime_conditions:
            query_parts.append(f"({' or '.join(mime_conditions)})")
        
        # Exclude trashed files by default
        if not source.include_trashed:
            query_parts.append("trashed=false")
        
        # Build final query
        query = " and ".join(query_parts) if query_parts else None
        logger.debug("Query string: %s", query)
        logger.debug("Folder ID: %s", source.folder_id)
        
        # Load documents
        if source.folder_id:
            raw_docs = self._reader.load_data(
                folder_id=source.folder_id,
                query_string=query
            )
        else:
            # Load from root or entire drive
            raw_docs = self._reader.load_data(
                query_string=query
            )
        
        # Handle None response
        if raw_docs is None:
            logger.warning("Google Drive returned None for folder %s", source.folder_id)
            raw_docs = []
        
        # Filter and enrich documents
        for doc in raw_docs:
            # Check exclude patterns
            if source.exclude_patterns and self._should_exclude(doc, source.exclude_patterns):
                continue
                
            # Enrich metadata
            self._enrich_metadata(doc, source)
            documents.append(doc)
        
        # Get change token for future incremental syncs
        page_token = self._get_start_page_token()
        
        return documents, {
            "total_files": len(documents),
            "page_token": page_token,
            "sync_time": datetime.now().isoformat()
        }
    
    def _incremental_sync(self, source: GoogleDriveSource, progress_callback: Optional[Callable[[int, int], None]] = None) -> Tuple[List[LlamaDocument], Dict[str, Any]]:
        """Perform incremental sync using Google Drive changes API."""
        if not source.page_token:
            # No previous sync, fall back to full sync
            return self._full_sync(source)
        
        documents = []
        changes = []
        
        try:
            # Get changes since last sync
            changes_response = self._reader._get_changes(
                page_token=source.page_token
            )
            
            changes = changes_response.get("changes", [])
            new_page_token = changes_response.get("newStartPageToken")
            
            # Process changes
            for change in changes:
                file_data = change.get("file")
                if not file_data:
                    continue
                
                # Check if file matches our criteria
                if not self._matches_criteria(file_data, source):
                    continue
                
                # Skip if file was removed
                if change.get("removed"):
                    continue
                
                # Load the specific file
                try:
                    doc_list = self._reader.load_data(file_ids=[file_data["id"]])
                    for doc in doc_list:
                        self._enrich_metadata(doc, source)
                        documents.append(doc)
                except Exception as e:
                    logger.warning("Error loading file %s: %s", file_data.get('name', 'Unknown'), e)
            
            return documents, {
                "total_files": len(documents),
                "changes_processed": len(changes),
                "page_token": new_page_token,
                "sync_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error during incremental sync: %s", e)
            # Fall back to full sync
            return self._full_sync(source)
    
    def _should_exclude(self, doc: LlamaDocument, exclude_patterns: List[str]) -> bool:
        """Check if document should be excluded based on patterns."""
        file_name = doc.metadata.get("file_name", "")
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        return False
    
    def _matches_criteria(self, file_data: Dict[str, Any], source: GoogleDriveSource) -> bool:
        """Check if file matches source criteria."""
        # Check MIME type
        mime_type = file_data.get("mimeType", "")
        file_type = self.GOOGLE_MIME_TYPES.get(mime_type) or self.STANDARD_MIME_TYPES.get(mime_type)
        
        if file_type and file_type not in source.file_types:
            return False
        
        # Check if in correct folder (if folder_id specified)
        if source.folder_id:
            parents = file_data.get("parents", [])
            if source.folder_id not in parents:
                return False
        
        # Check trash status
        if not source.include_trashed and file_data.get("trashed", False):
            return False
        
        # Check exclude patterns
        if source.exclude_patterns:
            file_name = file_data.get("name", "")
            for pattern in source.exclude_patterns:
                if fnmatch.fnmatch(file_name, pattern):
                    return False
        
        return True
    
    def _enrich_metadata(self, doc: LlamaDocument, source: GoogleDriveSource) -> None:
        """Enrich document metadata with additional information."""
        if doc.metadata is None:
            doc.metadata = {}
        
        # Add source information
        doc.metadata.update({
            "source_type": "google_drive",
            "source_id": source.id,
            "ingestion_timestamp": datetime.now().isoformat()
        })
        
        # Ensure file_path is set for consistency
        if "file_path" not in doc.metadata and "file_name" in doc.metadata:
            doc.metadata["file_path"] = doc.metadata["file_name"]
    
    def _get_start_page_token(self) -> Optional[str]:
        """Get start page token for tracking future changes."""
        try:
            # This would need to be implemented using direct API calls
            # For now, return None
            return None
        except Exception:
            return None
    
    def test_connection(self) -> bool:
        """Test if the Google Drive connection works."""
        try:
            # Try to list some files
            self._reader.load_data(query_string="trashed=false")
            return True
        except Exception as e:
            logger.error("Connection test failed: %s", e)
            return False

    def _get_folder_contents_recursive(self, folder_id: str, source: GoogleDriveSource, service) -> List[Dict[str, Any]]:
        """Recursively get all files from a folder and its subfolders.
        
        Args:
            folder_id: The folder ID to start from
            source: The source configuration
            service: The Google Drive service instance
            
        Returns:
            List of file metadata dictionaries
        """
        all_files = []
        folders_to_process = [(folder_id, "")]  # (folder_id, path)
        processed_folders = set()
        
        while folders_to_process:
            current_folder_id, current_path = folders_to_process.pop(0)
            
            # Skip if already processed (avoid cycles)
            if current_folder_id in processed_folders:
                continue
            processed_folders.add(current_folder_id)
            
            # Get all items in current folder
            query = f"'{current_folder_id}' in parents and trashed=false"
            page_token = None
            
            while True:
                try:
                    results = service.files().list(
                        q=query,
                        fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, owners, webViewLink, parents)",
                        pageSize=100,
                        pageToken=page_token
                    ).execute()
                    
                    items = results.get('files', [])
                    
                    for item in items:
                        # Add folder path to metadata
                        item['folder_path'] = current_path
                        
                        # Check if it's a folder
                        if item['mimeType'] == 'application/vnd.google-apps.folder':
                            # Add to folders to process
                            new_path = f"{current_path}/{item['name']}" if current_path else item['name']
                            folders_to_process.append((item['id'], new_path))
                        else:
                            # It's a file - check if it matches our criteria
                            if self._matches_file_types(item['mimeType'], source.file_types):
                                all_files.append(item)
                    
                    page_token = results.get('nextPageToken')
                    if not page_token:
                        break
                        
                except Exception as e:
                    logger.error("Error processing folder %s: %s", current_folder_id, e)
                    break
        
        return all_files
    
    def _matches_file_types(self, mime_type: str, file_types: List[str]) -> bool:
        """Check if a MIME type matches the configured file types.
        
        Args:
            mime_type: The file's MIME type
            file_types: List of file type filters
            
        Returns:
            True if the file matches, False otherwise
        """
        mime_map = {
            "document": "application/vnd.google-apps.document",
            "spreadsheet": "application/vnd.google-apps.spreadsheet", 
            "presentation": "application/vnd.google-apps.presentation",
            "pdf": "application/pdf"
        }
        
        # Check Google native types
        for file_type in file_types:
            if file_type in mime_map and mime_type == mime_map[file_type]:
                return True
        
        # Check explicit MIME types (like DOCX)
        if mime_type in file_types:
            return True
            
        return False 