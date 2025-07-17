# Orchard RAG Plugins

This directory contains the plugin system for extensible data ingestion in Orchard RAG.

## Overview

The plugin architecture allows for modular addition of new data sources without modifying the core application. Each plugin is self-contained and follows a standard interface.

## Available Plugins

- **GitHub**: Ingest code and documentation from GitHub repositories
- **Website** (coming soon): Crawl and ingest web content

## Plugin Structure

Each plugin follows this structure:

```
plugins/
├── plugin_name/
│   ├── __init__.py         # Plugin package initialization
│   ├── plugin.py           # Main plugin class (implements IngestionPlugin)
│   ├── reader.py           # Data source reader implementation
│   ├── models.py           # Plugin-specific data models
│   ├── config_schema.py    # Configuration validation schema
│   └── README.md           # Plugin documentation
```

## Creating a New Plugin

To create a new plugin:

1. **Create Plugin Directory**
   ```bash
   mkdir plugins/my_plugin
   ```

2. **Implement Required Classes**

   Create `plugin.py` with a class that extends `IngestionPlugin`:
   ```python
   from plugins.base import IngestionPlugin

   class MyPluginIngestionPlugin(IngestionPlugin):
       def validate_config(self) -> bool:
           # Validate configuration
           pass

       async def ingest(self, source_id: str, full_sync: bool = True) -> str:
           # Perform ingestion
           pass

       async def get_sources(self) -> List[Dict[str, Any]]:
           # Return configured sources
           pass

       def get_plugin_info(self) -> Dict[str, Any]:
           # Return plugin information
           pass
   ```

3. **Define Configuration Schema**

   Add your plugin configuration to `rag_config.yaml`:
   ```yaml
   plugins:
     my_plugin:
       enabled: true
       config:
         # Plugin-specific configuration
   ```

4. **Implement Data Reader**

   Create reader logic to fetch data from your source.

5. **Convert to Chunks**

   Use the shared LlamaIndex framework to convert documents to chunks:
   ```python
   from plugins.llamaindex.converters import convert_llama_doc_to_chunks
   ```

## Shared Framework

The `llamaindex/` directory contains shared utilities for all plugins:

- **client.py**: LlamaIndex client with ChromaDB integration
- **converters.py**: Document-to-chunk conversion utilities
- **embeddings.py**: Embedding model configuration
- **utils.py**: Common utility functions

## Plugin Lifecycle

1. **Discovery**: Plugins are automatically discovered on startup
2. **Initialization**: Plugin instances are created with their configuration
3. **Validation**: Configuration is validated before use
4. **Ingestion**: Data is fetched, processed, and stored in ChromaDB
5. **Monitoring**: Job status can be tracked through the API

## API Integration

Plugins are exposed through the following API endpoints:

- `GET /api/plugins` - List all available plugins
- `GET /api/plugins/{plugin_name}/config` - Get plugin configuration
- `PUT /api/plugins/{plugin_name}/config` - Update plugin configuration
- `POST /api/plugins/{plugin_name}/ingest` - Trigger ingestion
- `GET /api/plugins/{plugin_name}/status/{job_id}` - Get job status
- `GET /api/plugins/{plugin_name}/sources` - List configured sources

## Best Practices

1. **Error Handling**: Always implement proper error handling and logging
2. **Async Operations**: Use async/await for long-running operations
3. **Metadata**: Add rich metadata to help with retrieval
4. **Configuration**: Validate all configuration before use
5. **Documentation**: Include comprehensive README for each plugin
6. **Testing**: Add unit tests for plugin functionality

## Configuration Management

Plugin configurations are stored in `rag_config.yaml` at the project root. Environment variables can be referenced using `${VAR_NAME}` syntax.

Example:
```yaml
plugins:
  github:
    enabled: true
    config:
      github_token: "${GITHUB_TOKEN}"
```

## Plugin Directory Structure (with Isolated Dependencies)

Each plugin should live in its own subdirectory under `plugins/` and can have its own dependencies and virtual environment. Example structure:

```
plugins/
  my_plugin/
    main.py                # Plugin entrypoint
    requirements.txt       # Plugin-specific dependencies
    .venv/                 # Virtual environment for this plugin (created by user or setup script)
    ...                   # Other plugin files
  streaming_echo/
    streaming_echo_plugin.py
    requirements.txt
    .venv/
    ...
```

### Setup Steps for a New Plugin
1. **Create a new folder in `plugins/`**
2. **Add your plugin code (e.g., `main.py` or `streaming_*.py`)**
3. **Add a `requirements.txt` or `pyproject.toml` for dependencies**
4. **Create a virtual environment and install dependencies using uv:**
   ```bash
   cd plugins/my_plugin
   uv venv .venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```
   Or if using `pyproject.toml`:
   ```bash
   cd plugins/my_plugin
   uv venv .venv
   source .venv/bin/activate
   uv pip install .
   ```
5. **The main process will launch the plugin using its `.venv/bin/python` interpreter.**

- Each plugin is fully isolated and can use conflicting or specialized dependencies.
- Communication with the main process is via stdin/stdout (streaming or message-based protocols).

## Contributing

When contributing a new plugin:

1. Follow the established plugin structure
2. Implement all required methods from `IngestionPlugin`
3. Add comprehensive documentation
4. Include example configuration
5. Add appropriate error handling
6. Test with various data sources

## License

All plugins are part of the Orchard RAG system and follow the same license terms.