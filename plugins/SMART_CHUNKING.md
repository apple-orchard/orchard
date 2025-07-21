# Smart Chunking Plugins

This directory contains modular chunking plugins for advanced document processing in Orchard RAG.

## Available Plugins

### PyMuPDF4LLM Plugin

Located in `pymupdf4llm/`, this plugin provides smart PDF chunking using PyMuPDF4LLM library.

**Features:**
- Structure-aware PDF extraction (preserves headings, sections, tables)
- Markdown conversion for better LLM understanding
- Rich metadata extraction (TOC, tables, images)
- Multiple chunking strategies (markdown, sentence, semantic)

**Configuration:**
```python
{
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "page_chunks": True,
    "preserve_tables": True,
    "preserve_lists": True,
    "use_semantic_chunking": False
}
```

## Plugin Architecture

### Chunking Registry (`chunking_registry.py`)

The registry manages all available chunking plugins:

```python
from plugins.chunking_registry import chunking_registry

# List available plugins
plugins = chunking_registry.list_plugins()

# Process file with best available plugin
chunks = chunking_registry.process_file_with_best_plugin("document.pdf")
```

### Creating New Plugins

To create a new chunking plugin:

1. Create a new directory under `plugins/`
2. Implement the `ChunkingPlugin` protocol:

```python
class MyChunkingPlugin:
    def can_process(self, file_path: str) -> bool:
        """Check if plugin can handle the file."""
        return file_path.endswith('.myformat')
    
    def process_file(self, file_path: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """Process file and return chunks."""
        # Your implementation
        return chunks
```

3. Register in `chunking_registry.py`:

```python
registry.register_plugin("my_plugin", MyPlugin(), priority=5)
```

## Integration

The chunking plugins are automatically integrated with:
- Document processor (`app/utils/document_processor.py`)
- RAG service (`app/services/rag_service.py`)
- LlamaIndex converters (`plugins/llamaindex/converters.py`)
- CLI commands

## Usage Examples

### CLI
```bash
# Use smart chunking (default)
./orchard rag ingest-file document.pdf

# Disable smart chunking
./orchard rag ingest-file document.pdf --no-smart-chunking
```

### Python
```python
from plugins.pymupdf4llm import PyMuPDF4LLMProcessor

processor = PyMuPDF4LLMProcessor()
chunks = processor.process_file("document.pdf")
``` 