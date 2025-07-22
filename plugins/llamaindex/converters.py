"""Converters for LlamaIndex documents to internal format with smart chunking."""

import logging
from typing import List, Dict, Any, Optional
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.node_parser import (
    SentenceSplitter,
    MarkdownNodeParser,
)
from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

# Import chunking registry for smart chunking
try:
    from plugins.chunking_registry import chunking_registry
except ImportError:
    chunking_registry = None


def convert_llama_doc_to_chunks(
    documents: List[LlamaDocument],
    source_metadata: Dict[str, Any],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    preserve_structure: bool = True
) -> List[Dict[str, Any]]:
    """Convert LlamaIndex documents to our internal chunk format with smart chunking.
    
    Args:
        documents: List of LlamaIndex Document objects
        source_metadata: Additional metadata to add to all chunks
        chunk_size: Custom chunk size (uses settings default if None)
        chunk_overlap: Custom chunk overlap (uses settings default if None)
        preserve_structure: Whether to use structure-aware chunking for markdown
        
    Returns:
        List of chunks in our internal format
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if chunk_overlap is None:
        chunk_overlap = settings.chunk_overlap
    
    logger.info(f"Starting document conversion for {len(documents)} documents")
    logger.info(f"Chunking parameters: size={chunk_size}, overlap={chunk_overlap}, preserve_structure={preserve_structure}")
    
    # Initialize splitters
    sentence_splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    markdown_parser = MarkdownNodeParser()
    
    all_chunks = []
    markdown_doc_count = 0
    sentence_doc_count = 0
    
    for doc_idx, doc in enumerate(documents):
        # Extract text and metadata from LlamaIndex document
        text = doc.text or ""
        doc_metadata = doc.metadata or {}
        
        # Combine metadata
        combined_metadata = {
            **source_metadata,
            **doc_metadata,
            "source_type": source_metadata.get("source", "llamaindex"),
            "char_count": len(text),
            "word_count": len(text.split())
        }
        
        # If source_id is provided, create a properly formatted source string
        if "source_id" in source_metadata:
            plugin_source = source_metadata.get("source", "unknown")
            source_id = source_metadata.get("source_id", "unknown")
            combined_metadata["source"] = f"{plugin_source}:{source_id}"
        
        # Check if document has markdown structure
        is_markdown = (
            doc_metadata.get("file_type") == ".md" or
            "```" in text or
            text.count("#") > 2
        )
        
        if is_markdown:
            logger.debug(f"Document {doc_idx} detected as markdown (headers: {text.count('#')}, "
                        f"has code blocks: {'```' in text})")
        
        # Choose appropriate splitter
        if preserve_structure and is_markdown:
            logger.info(f"Using Markdown parser for document {doc_idx}")
            nodes = markdown_parser.get_nodes_from_documents([doc])
            markdown_doc_count += 1
        else:
            logger.info(f"Using Sentence splitter for document {doc_idx}")
            nodes = sentence_splitter.get_nodes_from_documents([doc])
            sentence_doc_count += 1
        
        logger.debug(f"Created {len(nodes)} nodes from document {doc_idx}")
        
        # Convert nodes to chunks
        for node_idx, node in enumerate(nodes):
            chunk_metadata = combined_metadata.copy()
            chunk_metadata.update({
                "document_index": doc_idx,
                "chunk_index": node_idx,
                "chunk_count": len(nodes),
                "chunk_type": "markdown_structured" if is_markdown and preserve_structure else "sentence_split",
                "chunk_char_count": len(node.text),
                "chunk_word_count": len(node.text.split()),
                "node_id": node.node_id,
            })
            
            # Add any additional metadata from the node
            if hasattr(node, 'metadata') and node.metadata:
                chunk_metadata.update(node.metadata)
            
            all_chunks.append({
                "content": node.text,
                "metadata": chunk_metadata
            })
    
    # Log chunking summary
    logger.info(f"Document conversion complete:")
    logger.info(f"  - Total documents: {len(documents)}")
    logger.info(f"  - Markdown-parsed documents: {markdown_doc_count}")
    logger.info(f"  - Sentence-split documents: {sentence_doc_count}")
    logger.info(f"  - Total chunks created: {len(all_chunks)}")
    
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

