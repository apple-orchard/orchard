"""Markdown chunking plugin for intelligent markdown file processing."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.schema import Document as LlamaDocument
from plugins.base import ChunkingPlugin

logger = logging.getLogger(__name__)


class MarkdownChunkingPlugin(ChunkingPlugin):
    """Plugin for intelligent Markdown file chunking using header-based splitting."""
    
    name = "markdown"
    supported_extensions = ['.md', '.markdown']
    
    def __init__(self):
        super().__init__()
        self.parser = MarkdownNodeParser(
            include_metadata=True,
            include_prev_next_rel=True,
            header_path_separator=" > "
        )
    
    def can_process(self, file_path: str) -> bool:
        """Check if this plugin can process the given file."""
        path = Path(file_path)
        return path.suffix.lower() in self.supported_extensions
    
    def process_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process a Markdown file into chunks using header-based splitting."""
        try:
            path = Path(file_path)
            logger.info(f"Processing Markdown file: {path.name}")
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create metadata
            file_metadata = {
                "source": str(path),
                "filename": path.name,
                "file_type": path.suffix.lower(),
                "content_type": "markdown"
            }
            
            if metadata:
                file_metadata.update(metadata)
            
            # Create LlamaIndex Document
            document = LlamaDocument(
                text=content,
                metadata=file_metadata
            )
            
            # Parse the document into nodes using MarkdownNodeParser
            nodes = self.parser.get_nodes_from_documents([document])
            
            # Convert nodes to our chunk format
            chunks = []
            for i, node in enumerate(nodes):
                chunk_metadata = file_metadata.copy()
                
                # Add node-specific metadata
                if hasattr(node, 'metadata'):
                    # Include header path if available
                    if 'header_path' in node.metadata:
                        chunk_metadata['header_path'] = node.metadata['header_path']
                    
                    # Include any other metadata from the node
                    for key, value in node.metadata.items():
                        if key not in chunk_metadata:
                            chunk_metadata[key] = value
                
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_count": len(nodes),
                    "chunk_id": node.node_id,
                    "chunking_method": "markdown_header_based"
                })
                
                # Extract relationships if available
                if hasattr(node, 'relationships'):
                    relationships = {}
                    for rel_type, rel_node in node.relationships.items():
                        relationships[rel_type.value] = rel_node.node_id
                    if relationships:
                        chunk_metadata['relationships'] = relationships
                
                chunks.append({
                    "content": node.get_content(),
                    "metadata": chunk_metadata
                })
            
            logger.info(f"Successfully chunked Markdown file into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing Markdown file {file_path}: {str(e)}")
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in the text."""
        # Rough estimation: 1 token per 4 characters for English text
        return len(text) // 4 