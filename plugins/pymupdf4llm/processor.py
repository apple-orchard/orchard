"""PyMuPDF4LLM processor for smart PDF chunking."""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pymupdf4llm
from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser,
    MarkdownNodeParser,
)
from llama_index.core.schema import Document as LlamaDocument
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from .config import PyMuPDF4LLMConfig

# Set up logging
logger = logging.getLogger(__name__)


class PyMuPDF4LLMProcessor:
    """Smart document processor using PyMuPDF4LLM for structure-aware PDF processing."""
    
    def __init__(self, config: Optional[PyMuPDF4LLMConfig] = None):
        """Initialize processor with configuration."""
        self.config = config or PyMuPDF4LLMConfig()
        logger.info(f"Initializing PyMuPDF4LLM processor with chunk_size={self.config.chunk_size}, "
                    f"chunk_overlap={self.config.chunk_overlap}")
        
        # Initialize parsers
        self.sentence_splitter = SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        
        self.markdown_parser = MarkdownNodeParser()
        
        # Initialize semantic splitter if enabled
        self.semantic_splitter = None
        if self.config.use_semantic_chunking:
            try:
                logger.info(f"Initializing semantic splitter with model: {self.config.semantic_model}")
                self.embed_model = HuggingFaceEmbedding(
                    model_name=self.config.semantic_model
                )
                self.semantic_splitter = SemanticSplitterNodeParser(
                    embed_model=self.embed_model,
                    breakpoint_percentile_threshold=self.config.breakpoint_percentile_threshold,
                    buffer_size=1,
                )
                logger.info("Semantic splitter initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize semantic splitter: {e}")
    
    def can_process(self, file_path: str) -> bool:
        """Check if this processor can handle the file."""
        return file_path.lower().endswith('.pdf')
    
    def extract_from_pdf(self, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Extract text and metadata from PDF using PyMuPDF4LLM."""
        logger.info(f"Extracting PDF content from: {file_path}")
        logger.debug(f"PDF extraction settings: page_chunks={self.config.page_chunks}, "
                     f"write_images={self.config.write_images}")
        
        # Extract as markdown with page chunks
        result = pymupdf4llm.to_markdown(
            doc=file_path,
            page_chunks=self.config.page_chunks,
            write_images=self.config.write_images,
            image_format=self.config.image_format,
            max_chars=self.config.max_chars,
        )
        
        if self.config.page_chunks and isinstance(result, list):
            # Combine page chunks into full text while preserving metadata
            full_text = ""
            page_metadata = []
            
            for chunk in result:
                if isinstance(chunk, dict):
                    full_text += chunk.get("text", "") + "\n\n"
                    
                    # Extract page metadata
                    page_info = {
                        "page": chunk.get("metadata", {}).get("page", 0),
                        "toc_items": chunk.get("toc_items", []),
                        "tables": len(chunk.get("tables", [])),
                        "images": len(chunk.get("images", [])),
                        "has_tables": len(chunk.get("tables", [])) > 0,
                        "has_images": len(chunk.get("images", [])) > 0,
                    }
                    
                    # Add table metadata if present
                    if chunk.get("tables"):
                        page_info["table_info"] = [
                            {
                                "bbox": table.get("bbox"),
                                "rows": table.get("rows"),
                                "columns": table.get("columns")
                            }
                            for table in chunk.get("tables", [])
                        ]
                    
                    page_metadata.append(page_info)
                else:
                    full_text += str(chunk) + "\n\n"
            
            return full_text.strip(), page_metadata
        else:
            # Simple markdown text without page chunks
            return str(result), []
    
    def chunk_markdown(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk markdown text preserving structure."""
        logger.info("Using Markdown chunking strategy (structure-aware)")
        doc = LlamaDocument(text=text, metadata=metadata)
        
        # Use markdown parser to preserve structure
        nodes = self.markdown_parser.get_nodes_from_documents([doc])
        logger.debug(f"Markdown parser created {len(nodes)} nodes")
        
        chunks = []
        for i, node in enumerate(nodes):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "chunk_count": len(nodes),
                "chunk_type": "markdown_structured",
                "node_id": node.node_id,
            })
            
            # Add relationships if available
            if hasattr(node, 'relationships') and node.relationships:
                chunk_metadata["relationships"] = str(node.relationships)
            
            chunks.append({
                "content": node.text,
                "metadata": chunk_metadata
            })
        
        return chunks
    
    def chunk_with_semantic(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text using semantic similarity."""
        if not self.semantic_splitter:
            logger.info("Semantic splitter not available, falling back to sentence splitting")
            return self.chunk_with_sentences(text, metadata)
        
        logger.info("Using Semantic chunking strategy (embedding-based)")
        doc = LlamaDocument(text=text, metadata=metadata)
        
        try:
            nodes = self.semantic_splitter.get_nodes_from_documents([doc])
            logger.debug(f"Semantic splitter created {len(nodes)} nodes")
            
            chunks = []
            for i, node in enumerate(nodes):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_count": len(nodes),
                    "chunk_type": "semantic",
                    "chunk_char_count": len(node.text),
                    "chunk_word_count": len(node.text.split())
                })
                
                chunks.append({
                    "content": node.text,
                    "metadata": chunk_metadata
                })
            
            return chunks
            
        except Exception as e:
            print(f"Semantic chunking failed: {e}, falling back to sentence splitting")
            return self.chunk_with_sentences(text, metadata)
    
    def chunk_with_sentences(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text using sentence splitting."""
        logger.info("Using Sentence chunking strategy")
        doc = LlamaDocument(text=text, metadata=metadata)
        nodes = self.sentence_splitter.get_nodes_from_documents([doc])
        logger.debug(f"Sentence splitter created {len(nodes)} nodes")
        
        chunks = []
        for i, node in enumerate(nodes):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "chunk_count": len(nodes),
                "chunk_type": "sentence_split",
                "chunk_char_count": len(node.text),
                "chunk_word_count": len(node.text.split())
            })
            
            chunks.append({
                "content": node.text,
                "metadata": chunk_metadata
            })
        
        return chunks
    
    def process_file(self, file_path: str, additional_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process a PDF file with smart chunking."""
        if not self.can_process(file_path):
            raise ValueError(f"PyMuPDF4LLM processor cannot handle file: {file_path}")
        
        logger.info(f"Processing PDF file with PyMuPDF4LLM: {file_path}")
        file_path_obj = Path(file_path)
        
        # Base metadata
        metadata = {
            "source": str(file_path_obj),
            "filename": file_path_obj.name,
            "file_type": file_path_obj.suffix.lower(),
            "file_size": file_path_obj.stat().st_size,
            "processor": "pymupdf4llm"
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # Extract text and page metadata
        text, page_metadata = self.extract_from_pdf(file_path)
        
        if page_metadata:
            metadata["page_count"] = len(page_metadata)
            metadata["has_toc"] = any(page["toc_items"] for page in page_metadata)
            metadata["total_tables"] = sum(page["tables"] for page in page_metadata)
            metadata["total_images"] = sum(page["images"] for page in page_metadata)
            metadata["page_metadata"] = page_metadata
            
            logger.info(f"PDF metadata extracted - Pages: {metadata['page_count']}, "
                       f"Tables: {metadata['total_tables']}, Images: {metadata['total_images']}, "
                       f"Has TOC: {metadata['has_toc']}")
        
        metadata["char_count"] = len(text)
        metadata["word_count"] = len(text.split())
        
        # Determine chunking strategy
        is_structured = (
            metadata.get("has_toc", False) or
            text.count("#") > 5 or  # Has markdown headers
            "```" in text  # Has code blocks
        )
        
        logger.info(f"Document structure analysis - Is structured: {is_structured}, "
                   f"Markdown headers found: {text.count('#')}")
        
        if self.config.use_semantic_chunking:
            chunks = self.chunk_with_semantic(text, metadata)
        elif is_structured:
            chunks = self.chunk_markdown(text, metadata)
        else:
            chunks = self.chunk_with_sentences(text, metadata)
        
        logger.info(f"Chunking complete - Created {len(chunks)} chunks from {file_path}")
        return chunks


def create_processor(config: Optional[Dict[str, Any]] = None) -> PyMuPDF4LLMProcessor:
    """Factory function to create a processor instance."""
    if config:
        config_obj = PyMuPDF4LLMConfig(**config)
    else:
        config_obj = PyMuPDF4LLMConfig()
    
    return PyMuPDF4LLMProcessor(config_obj) 