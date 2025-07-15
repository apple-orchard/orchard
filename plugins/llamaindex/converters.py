"""Converters for LlamaIndex documents to internal format."""

from typing import List, Dict, Any, Optional
from llama_index.core.schema import Document as LlamaDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings


def convert_llama_doc_to_chunks(
    documents: List[LlamaDocument],
    source_metadata: Dict[str, Any],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Convert LlamaIndex documents to our internal chunk format.
    
    Args:
        documents: List of LlamaIndex Document objects
        source_metadata: Additional metadata to add to all chunks
        chunk_size: Custom chunk size (uses settings default if None)
        chunk_overlap: Custom chunk overlap (uses settings default if None)
        
    Returns:
        List of chunks in our internal format
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if chunk_overlap is None:
        chunk_overlap = settings.chunk_overlap
    
    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    all_chunks = []
    
    for doc in documents:
        # Extract text and metadata from LlamaIndex document
        text = doc.text or ""
        doc_metadata = doc.metadata or {}
        
        # Combine metadata
        combined_metadata = {
            **source_metadata,
            **doc_metadata,
            "source_type": "llamaindex",
            "char_count": len(text),
            "word_count": len(text.split())
        }
        
        # Split text into chunks
        chunks = text_splitter.split_text(text)
        
        # Create chunk documents
        for i, chunk in enumerate(chunks):
            chunk_metadata = combined_metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "chunk_count": len(chunks),
                "chunk_char_count": len(chunk),
                "chunk_word_count": len(chunk.split())
            })
            
            all_chunks.append({
                "content": chunk,
                "metadata": chunk_metadata
            })
    
    return all_chunks


def convert_github_metadata(repo_info: Dict[str, Any]) -> Dict[str, Any]:
    """Convert GitHub-specific metadata to our format.
    
    Args:
        repo_info: Repository information from GitHub
        
    Returns:
        Standardized metadata dictionary
    """
    return {
        "source": f"github:{repo_info.get('owner', '')}/{repo_info.get('repo', '')}",
        "repository": repo_info.get('repo', ''),
        "owner": repo_info.get('owner', ''),
        "branch": repo_info.get('branch', 'main'),
        "file_path": repo_info.get('file_path', ''),
        "file_type": repo_info.get('file_type', ''),
        "last_modified": repo_info.get('last_modified', ''),
        "commit_sha": repo_info.get('commit_sha', '')
    }


def batch_process_documents(
    documents: List[LlamaDocument],
    batch_size: int = 100
) -> List[List[LlamaDocument]]:
    """Split documents into batches for processing.
    
    Args:
        documents: List of documents to process
        batch_size: Size of each batch
        
    Returns:
        List of document batches
    """
    batches = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batches.append(batch)
    return batches 