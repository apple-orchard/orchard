"""Utility functions for LlamaIndex integration."""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib
from datetime import datetime


def get_file_hash(file_path: str) -> str:
    """Calculate hash of a file for change detection.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA256 hash of the file content
    """
    hash_obj = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def get_directory_files(
    directory: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    recursive: bool = True
) -> List[str]:
    """Get list of files in a directory with filtering.
    
    Args:
        directory: Directory path
        include_patterns: List of glob patterns to include
        exclude_patterns: List of glob patterns to exclude
        recursive: Whether to search recursively
        
    Returns:
        List of file paths
    """
    from pathlib import Path
    import fnmatch
    
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    
    pattern = "**/*" if recursive else "*"
    all_files = []
    
    for file_path in dir_path.glob(pattern):
        if not file_path.is_file():
            continue
        
        # Convert to string for pattern matching
        file_str = str(file_path.relative_to(dir_path))
        
        # Check include patterns
        if include_patterns:
            if not any(fnmatch.fnmatch(file_str, pattern) for pattern in include_patterns):
                continue
        
        # Check exclude patterns
        if exclude_patterns:
            if any(fnmatch.fnmatch(file_str, pattern) for pattern in exclude_patterns):
                continue
        
        all_files.append(str(file_path))
    
    return all_files


def track_file_changes(
    files: List[str],
    cache_file: str
) -> Dict[str, Any]:
    """Track file changes for incremental updates.
    
    Args:
        files: List of file paths to track
        cache_file: Path to cache file storing hashes
        
    Returns:
        Dictionary with 'new', 'modified', and 'deleted' file lists
    """
    import json
    
    # Load existing cache
    old_hashes = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                old_hashes = json.load(f)
        except:
            old_hashes = {}
    
    # Calculate current hashes
    current_hashes = {}
    for file_path in files:
        if os.path.exists(file_path):
            current_hashes[file_path] = get_file_hash(file_path)
    
    # Determine changes
    new_files = []
    modified_files = []
    deleted_files = []
    
    # Check for new and modified files
    for file_path, hash_value in current_hashes.items():
        if file_path not in old_hashes:
            new_files.append(file_path)
        elif old_hashes[file_path] != hash_value:
            modified_files.append(file_path)
    
    # Check for deleted files
    for file_path in old_hashes:
        if file_path not in current_hashes:
            deleted_files.append(file_path)
    
    # Save current hashes
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(current_hashes, f, indent=2)
    
    return {
        "new": new_files,
        "modified": modified_files,
        "deleted": deleted_files,
        "timestamp": datetime.now().isoformat()
    }


def validate_github_token(token: str) -> bool:
    """Validate GitHub personal access token.
    
    Args:
        token: GitHub token to validate
        
    Returns:
        True if token is valid, False otherwise
    """
    import requests
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        return response.status_code == 200
    except:
        return False 