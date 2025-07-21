"""Configuration for PyMuPDF4LLM plugin."""

from typing import Optional
from pydantic import BaseModel, Field


class PyMuPDF4LLMConfig(BaseModel):
    """Configuration for PyMuPDF4LLM smart chunking."""
    
    # Chunking parameters
    chunk_size: int = Field(
        default=1000,
        description="Target chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=200,
        description="Character overlap between chunks"
    )
    
    # PDF extraction options
    page_chunks: bool = Field(
        default=True,
        description="Whether to create page-based chunks with metadata"
    )
    write_images: bool = Field(
        default=False,
        description="Whether to extract images from PDFs"
    )
    image_format: str = Field(
        default="png",
        description="Image format for extracted images"
    )
    max_chars: int = Field(
        default=0,
        description="Maximum characters per chunk (0 for no limit)"
    )
    
    # Semantic chunking options
    use_semantic_chunking: bool = Field(
        default=False,
        description="Whether to use semantic chunking based on embeddings"
    )
    semantic_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model for semantic chunking"
    )
    breakpoint_percentile_threshold: int = Field(
        default=95,
        description="Percentile threshold for semantic breakpoints"
    )
    
    # Structure preservation
    preserve_tables: bool = Field(
        default=True,
        description="Keep tables intact in chunks"
    )
    preserve_lists: bool = Field(
        default=True,
        description="Keep lists intact in chunks"
    )
    
    class Config:
        """Pydantic config."""
        extra = "forbid" 