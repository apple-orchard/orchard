# PyMuPDF4LLM Plugin

A smart PDF chunking plugin for Orchard that uses PyMuPDF4LLM to preserve document structure and improve RAG performance.

## Features

- **Structure-Aware Extraction**: Preserves headings, sections, tables, and lists
- **Smart Chunking**: Multiple strategies based on document structure
  - Markdown-based chunking for structured documents
  - Sentence-based chunking for unstructured text
  - Semantic chunking based on meaning (optional)
- **Rich Metadata**: Extracts TOC, tables, images, and page information
- **100% Local**: No cloud services required

## Configuration

The plugin can be configured through the following parameters:

```python
{
    # Chunking parameters
    "chunk_size": 1000,              # Target chunk size in characters
    "chunk_overlap": 200,            # Character overlap between chunks
    
    # PDF extraction options
    "page_chunks": True,             # Create page-based chunks with metadata
    "write_images": False,           # Extract images from PDFs
    "image_format": "png",           # Image format for extracted images
    "max_chars": 0,                  # Maximum characters per chunk (0 = no limit)
    
    # Semantic chunking options
    "use_semantic_chunking": False,  # Use embedding-based chunking
    "semantic_model": "sentence-transformers/all-MiniLM-L6-v2",
    "breakpoint_percentile_threshold": 95,
    
    # Structure preservation
    "preserve_tables": True,         # Keep tables intact
    "preserve_lists": True,          # Keep lists intact
}
```

## Usage

The plugin is automatically integrated with the document processor. When processing PDFs, it will:

1. Extract text as Markdown, preserving structure
2. Extract metadata (TOC, tables, images)
3. Choose appropriate chunking strategy
4. Return chunks with rich metadata

## Chunking Strategies

1. **Markdown Chunking**: For documents with clear structure (headings, sections)
2. **Sentence Chunking**: For unstructured text
3. **Semantic Chunking**: Groups sentences by meaning (requires embeddings)

## Requirements

- `pymupdf>=1.24.0`
- `pymupdf4llm>=0.0.2`
- `llama-index-core>=0.11.23`
- `llama-index-embeddings-huggingface>=0.3.1` (for semantic chunking) 