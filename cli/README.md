# Orchard RAG CLI

A command-line interface for managing the Orchard RAG system, with a focus on plugin management and system administration.

## Installation

The CLI is included with the Orchard RAG system. You have two options for running it:

### Option 1: Using Docker (Recommended)

The easiest way to use the CLI is through the Docker wrapper:

```bash
# Make sure the services are running
./dev.sh dev

# Use the orchard command
./orchard --help
```

### Option 2: Local Installation

If you prefer to run the CLI locally:

```bash
# Install dependencies (if using uv)
uv sync

# Or install manually
pip install -r requirements.txt

# Run the CLI
python orchard_cli.py --help
```

## Usage

### Basic Commands

```bash
# Check system health
./orchard health

# Show system information
./orchard rag info

# Test all system components
./orchard rag test
```

### Plugin Management

```bash
# List all available plugins
./orchard plugins list

# Show detailed information about a plugin
./orchard plugins info github

# List sources for a plugin
./orchard plugins sources github

# Trigger ingestion for a plugin
./orchard plugins ingest github

# Trigger ingestion for a specific source
./orchard plugins ingest github --source-id my-repo

# Perform incremental sync
./orchard plugins ingest github --incremental

# Monitor a job
./orchard plugins monitor github <job-id>

# Enable/disable plugins
./orchard plugins enable github
./orchard plugins disable github

# Configure a plugin
./orchard plugins config github
```

### RAG System Commands

```bash
# Query the knowledge base
./orchard rag query "What is RAG?"

# Query with custom chunk limit
./orchard rag query "What is RAG?" --max-chunks 10

# Ingest text content
./orchard rag ingest-text "Your text content here"

# Ingest a file
./orchard rag ingest-file /path/to/document.pdf

# List available models
./orchard rag models

# Pull a model
./orchard rag pull-model llama3.1:8b
```

### Global Options

```bash
# Use a different API URL
./orchard --api-url http://localhost:8080 health

# Enable verbose output
./orchard --verbose plugins list
```

## Command Reference

### Health Check
- `health` - Check system health and status

### RAG Commands
- `rag info` - Show system information and data summary
- `rag test` - Test all system components
- `rag query [question]` - Query the knowledge base
- `rag ingest-text [text]` - Ingest text content
- `rag ingest-file [path]` - Ingest a file
- `rag models` - List available Ollama models
- `rag pull-model <name>` - Pull a model from Ollama

### Plugin Commands
- `plugins list` - List all available plugins
- `plugins info <name>` - Show plugin information
- `plugins sources <name>` - List plugin sources
- `plugins ingest <name>` - Trigger plugin ingestion
- `plugins monitor <name> <job-id>` - Monitor a job
- `plugins enable <name>` - Enable a plugin
- `plugins disable <name>` - Disable a plugin
- `plugins config <name>` - Configure a plugin

## Examples

### Complete Workflow

```bash
# 1. Check system health
./orchard health

# 2. List available plugins
./orchard plugins list

# 3. Configure GitHub plugin (if needed)
./orchard plugins config github

# 4. Trigger GitHub ingestion
./orchard plugins ingest github

# 5. Monitor the job (if you want to watch progress)
# The CLI will show you the job ID after starting ingestion

# 6. Check system info to see ingested data
./orchard rag info

# 7. Query the knowledge base
./orchard rag query "What repositories are available?"
```

### Plugin Management Workflow

```bash
# 1. List all plugins and their status
./orchard plugins list

# 2. Show detailed info about a specific plugin
./orchard plugins info github

# 3. List sources for the plugin
./orchard plugins sources github

# 4. Trigger ingestion for a specific source
./orchard plugins ingest github --source-id my-repo

# 5. Monitor the job progress
./orchard plugins monitor github <job-id>
```

## Architecture

The CLI is built with a modular architecture:

```
cli/
├── __init__.py          # Package initialization
├── main.py              # Main CLI entry point and argument parsing
├── helpers.py           # Helper classes and utilities
├── commands/            # Command implementations
│   ├── __init__.py
│   ├── plugins.py       # Plugin management commands
│   └── rag.py          # RAG system commands
└── README.md           # This file
```

### Helper Classes

- **APIClient**: Handles HTTP requests to the RAG API
- **ConfigHelper**: Manages configuration file operations
- **DisplayHelper**: Formats and displays output
- **ValidationHelper**: Validates user input

### Adding New Commands

To add new commands:

1. Create a new command file in `cli/commands/`
2. Import and register the command in `cli/main.py`
3. Add argument parsing for the new command
4. Add the command handler function

Example:

```python
# In cli/commands/new_feature.py
def new_command():
    """New command implementation"""
    pass

# In cli/main.py
from .commands import new_feature

# Add to argument parser
new_parser = subparsers.add_parser("new-feature", help="New feature")

# Add to command handler
elif args.command == "new-feature":
    new_feature.new_command()
```

## Error Handling

The CLI includes comprehensive error handling:

- Network errors are caught and displayed clearly
- Invalid input is validated before processing
- User confirmation is requested for destructive operations
- Verbose mode can be enabled for debugging

## Configuration

The CLI uses the same configuration as the main RAG system:

- API URL can be specified with `--api-url`
- Configuration is loaded from `rag_config.yaml`
- Environment variables are supported

## Troubleshooting

### Common Issues

1. **Connection refused**: Make sure the RAG API is running
2. **Plugin not found**: Check that the plugin is properly configured
3. **Authentication errors**: Verify API credentials and tokens
4. **Job monitoring fails**: Check that the job ID is correct

### Debug Mode

Use the `--verbose` flag to see detailed error information:

```bash
./orchard --verbose plugins list
```

## Contributing

To extend the CLI:

1. Follow the modular structure
2. Use the helper classes for common operations
3. Add proper error handling
4. Include help text for all commands
5. Test with different API configurations