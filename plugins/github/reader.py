"""GitHub reader implementation using LlamaIndex."""

from typing import List, Dict, Any, Optional
from llama_index.readers.github import GithubRepositoryReader, GithubClient
from llama_index.core.schema import Document as LlamaDocument
import fnmatch
from datetime import datetime
from plugins.llamaindex.utils import track_file_changes, validate_github_token


class GitHubReader:
    """Wrapper around LlamaIndex GitHub reader with additional functionality."""
    
    def __init__(self, github_token: str):
        """Initialize GitHub reader.
        
        Args:
            github_token: GitHub personal access token
        """
        if not validate_github_token(github_token):
            raise ValueError("Invalid GitHub token provided")
        
        self.github_token = github_token
        self._readers: Dict[str, GithubRepositoryReader] = {}
        # Create a GitHub client
        self._github_client = GithubClient(github_token=github_token)
    
    def get_reader(self, owner: str, repo: str) -> GithubRepositoryReader:
        """Get or create a reader for a specific repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            GithubRepositoryReader instance
        """
        repo_key = f"{owner}/{repo}"
        
        if repo_key not in self._readers:
            self._readers[repo_key] = GithubRepositoryReader(
                github_client=self._github_client,
                owner=owner,
                repo=repo,
                verbose=True
            )
        
        return self._readers[repo_key]
    
    def read_repository(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        paths: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[LlamaDocument]:
        """Read documents from a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch to read from
            paths: Specific paths to include (None for all)
            exclude_patterns: File patterns to exclude
            
        Returns:
            List of LlamaDocument objects
        """
        reader = self.get_reader(owner, repo)
        
        # Get all documents from the branch
        try:
            if paths:
                # If specific paths are provided, read each path
                all_docs = []
                for path in paths:
                    docs = reader.load_data(branch=branch, path=path)
                    all_docs.extend(docs)
            else:
                # Read entire repository
                all_docs = reader.load_data(branch=branch)
        except Exception as e:
            raise Exception(f"Error reading repository {owner}/{repo}: {str(e)}")
        
        # Filter documents based on exclude patterns
        if exclude_patterns:
            filtered_docs = []
            for doc in all_docs:
                file_path = doc.metadata.get("file_path", "")
                
                # Check if file should be excluded
                excluded = False
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(file_path, pattern):
                        excluded = True
                        break
                
                if not excluded:
                    filtered_docs.append(doc)
            
            return filtered_docs
        
        return all_docs
    
    def get_file_list(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        paths: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get list of files in a repository without reading content.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch to list files from
            paths: Specific paths to include
            
        Returns:
            List of file information dictionaries
        """
        reader = self.get_reader(owner, repo)
        
        # This is a simplified version - in practice, you'd use GitHub API
        # to get file list without downloading content
        docs = self.read_repository(owner, repo, branch, paths)
        
        file_list = []
        for doc in docs:
            file_info = {
                "path": doc.metadata.get("file_path", ""),
                "size": len(doc.text or ""),
                "last_modified": doc.metadata.get("last_modified", ""),
                "url": doc.metadata.get("url", "")
            }
            file_list.append(file_info)
        
        return file_list
    
    def read_incremental(
        self,
        owner: str,
        repo: str,
        branch: str,
        cache_file: str,
        paths: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Read repository incrementally, only processing changed files.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch to read from
            cache_file: Path to cache file for tracking changes
            paths: Specific paths to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            Dictionary with 'documents' and 'changes' information
        """
        # Get all documents first
        all_docs = self.read_repository(owner, repo, branch, paths, exclude_patterns)
        
        # Extract file paths from documents
        file_paths = [doc.metadata.get("file_path", "") for doc in all_docs]
        
        # Track changes
        changes = track_file_changes(file_paths, cache_file)
        
        # Filter documents based on changes
        changed_docs = []
        for doc in all_docs:
            file_path = doc.metadata.get("file_path", "")
            if file_path in changes["new"] or file_path in changes["modified"]:
                changed_docs.append(doc)
        
        return {
            "documents": changed_docs,
            "changes": changes,
            "total_files": len(all_docs),
            "changed_files": len(changed_docs)
        }
    
    def enrich_metadata(self, documents: List[LlamaDocument], owner: str, repo: str, branch: str) -> None:
        """Enrich document metadata with additional GitHub information.
        
        Args:
            documents: List of documents to enrich
            owner: Repository owner
            repo: Repository name
            branch: Branch name
        """
        for doc in documents:
            if doc.metadata is None:
                doc.metadata = {}
            
            # Add GitHub-specific metadata
            doc.metadata.update({
                "source_type": "github",
                "repository_owner": owner,
                "repository_name": repo,
                "repository_full_name": f"{owner}/{repo}",
                "branch": branch,
                "ingestion_timestamp": datetime.now().isoformat()
            }) 