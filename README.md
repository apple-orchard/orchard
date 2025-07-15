# RAG API - Retrieval-Augmented Generation with FastAPI

A full-stack RAG (Retrieval-Augmented Generation) system with a Python backend and React frontend. The backend uses FastAPI, ChromaDB, and Ollama for document processing and AI-powered question answering. The frontend provides a modern chat interface with TypeScript and Tailwind CSS for interacting with your documents.

## Features

### Backend Features
- **Document Ingestion**: Support for PDF, DOCX, and TXT files
- **Intelligent Chunking**: Automatic text splitting with configurable chunk sizes
- **Vector Storage**: ChromaDB for efficient embedding storage and retrieval
- **RAG Workflow**: Combines document retrieval with local Ollama models
- **REST API**: FastAPI-based endpoints for easy integration
- **Source Citations**: Answers include references to source documents
- **Local AI**: No external API dependencies - all processing runs locally
- **Health Monitoring**: Built-in health checks and system testing
- **Hot Reloading**: Development mode with automatic code reload
- **Command Line Interface**: Comprehensive CLI for system management and plugin operations

### Frontend Features
- **Modern Chat Interface**: TypeScript-based chat interface with Tailwind CSS
- **Document Upload**: Drag-and-drop file upload with progress indicators
- **Real-time Responses**: Live chat with typing indicators and timestamps
- **Source Display**: Shows document sources for each answer
- **Responsive Design**: Modern, mobile-friendly interface
- **Error Handling**: User-friendly error messages and retry options
- **Hot Reloading**: Development mode with automatic UI updates
- **Docker Support**: Containerized deployment with the backend

## Requirements

- Python 3.11+
- Ollama installed and running locally
- Docker (optional, for containerized deployment)
- Node.js 18+ (for frontend development)

## Quick Start

### Option 1: Development Mode (Recommended for Development)

1. **Install and start Ollama:**
```bash
# Install Ollama (visit https://ollama.com/download for your OS)
# Start Ollama server
ollama serve

# Pull the default model (in another terminal)
ollama pull llama3.1:8b

# OR use the automated setup script
python setup_ollama.py
```

2. **Clone the repository:**
```bash
git clone <repository-url>
cd orchard
```

3. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your Ollama configuration if needed
```

4. **Start development environment:**
```bash
# Start with hot reloading for both frontend and backend
./dev.sh dev

# Or for a fresh rebuild
./dev.sh rebuild
```

The application will be available at:
- **Frontend**: `http://localhost:3000` (with hot reloading)
- **Backend API**: `http://localhost:8011` (with hot reloading)
- **API Documentation**: `http://localhost:8011/docs`

### Option 2: Production Mode

```bash
# Quick production start
./start.sh

# Or using dev.sh
./dev.sh prod
```

## Development Script (dev.sh)

The `dev.sh` script provides a comprehensive development workflow:

```bash
# Development commands
./dev.sh dev       # Start development environment with hot reloading
./dev.sh rebuild   # Rebuild and restart development environment
./dev.sh logs      # Show logs from running containers
./dev.sh stop      # Stop all containers
./dev.sh cleanup   # Clean up processes and containers

# Production commands
./dev.sh prod      # Start production environment

# Help
./dev.sh help      # Show all available commands
```

### What the Development Mode Includes:

- ✅ **Backend Hot Reloading**: FastAPI automatically restarts on code changes
- ✅ **Frontend Hot Reloading**: React development server with live updates
- ✅ **Tailwind CSS**: Fully configured with PostCSS for modern styling
- ✅ **TypeScript**: Full TypeScript support with type checking
- ✅ **Docker Development**: Containerized development with volume mounts
- ✅ **Automatic Setup**: Checks Ollama, Docker, and creates .env file
- ✅ **Log Streaming**: Real-time logs from both services

## Installation Options

### Option A: Local Development (Without Docker)

1. **Install and start Ollama:**
```bash
# Install Ollama (visit https://ollama.com/download for your OS)
# Start Ollama server
ollama serve

# Pull the default model (in another terminal)
ollama pull llama3.1:8b
```

2. **Clone the repository:**
```bash
git clone <repository-url>
cd orchard
```

3. **Create virtual environment:**
```bash
# Install uv if needed
# curl -LsSf https://astral.sh/uv/install.sh | sh

uv venv
```

4. **Install dependencies:**
```bash
uv sync
```

5. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your Ollama configuration if needed
```

6. **Run the backend:**
```bash
uv run python main.py
```

7. **Run the frontend (in a new terminal):**
```bash
cd frontend
npm install
npm start
```

### Option B: Docker Development (Recommended)

1. **Prerequisites:**
   - Docker and Docker Compose installed
   - Ollama running on host system (`ollama serve`)
   - Required model pulled (`ollama pull llama3.1:8b`)

2. **Start development environment:**
```bash
# Clone and setup
git clone <repository-url>
cd orchard
cp env.example .env

# Start development with hot reloading
./dev.sh dev
```

### Option C: Production Deployment

```bash
# Quick production start
./start.sh

# Or manually
docker-compose up -d
```

## Configuration

Configure the application by editing the `.env` file:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
CHROMA_DB_PATH=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_TOKENS=500
TEMPERATURE=0.7
MAX_RETRIEVED_CHUNKS=5
```

### Configuration Options

- `OLLAMA_HOST`: Ollama server host URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model to use (default: llama3.1:8b)
- `CHROMA_DB_PATH`: Path to ChromaDB storage directory
- `EMBEDDING_MODEL`: Sentence transformer model for embeddings
- `CHUNK_SIZE`: Maximum size of text chunks
- `CHUNK_OVERLAP`: Overlap between consecutive chunks
- `MAX_TOKENS`: Maximum tokens for Ollama responses
- `TEMPERATURE`: Creativity level for AI responses (0-1)
- `MAX_RETRIEVED_CHUNKS`: Number of chunks to retrieve for context

## API Endpoints

### Health Check

```bash
GET /health
```

Returns the health status of the API.

### Query Documents

```bash
POST /query
Content-Type: application/json

{
  "question": "What is the main topic of the documents?",
  "max_chunks": 5
}
```

### Ingest Documents

#### Upload File
```bash
POST /ingest
Content-Type: multipart/form-data

- file: (file upload)
- metadata: {"category": "documentation"} (optional JSON)
```

#### Ingest Text Content
```bash
POST /ingest/text
Content-Type: application/json

{
  "text_content": "Your text content here",
  "metadata": {"source": "manual_input"}
}
```

#### Ingest File by Path
```bash
POST /ingest/file
Content-Type: application/json

{
  "file_path": "/path/to/your/document.pdf",
  "metadata": {"category": "reports"}
}
```

### System Information

```bash
GET /knowledge-base/info
```

Returns information about the knowledge base.

```bash
GET /test
```

Tests all system components.

```bash
GET /models
```

Lists available Ollama models.

```bash
POST /models/pull
```

Pulls a model from Ollama hub.

## Command Line Interface (CLI)

The Orchard RAG system includes a comprehensive CLI for managing the system, with a focus on plugin management and ingestion workflows.

### CLI Setup

The CLI is included in the project and can be used immediately:

```bash
# Make the CLI executable (first time only)
chmod +x orchard

# Test the CLI
./orchard --help
```

### CLI Commands

#### System Commands
```bash
# Check system health
./orchard health

# Show system information and data summary
./orchard rag info

# Test all system components
./orchard rag test

# Query the knowledge base
./orchard rag query "What is RAG?"

# Query with custom chunk limit
./orchard rag query "How does authentication work?" --max-chunks 10
```

#### Plugin Management
```bash
# List all available plugins
./orchard plugins list

# Show detailed information about a plugin
./orchard plugins info github

# List sources for a plugin
./orchard plugins sources github

# Trigger ingestion for a plugin (interactive)
./orchard plugins ingest github

# Trigger ingestion for a specific source
./orchard plugins ingest github --source-id my-repo

# Perform incremental sync
./orchard plugins ingest github --incremental

# Monitor a job
./orchard plugins monitor github <job-id>
```

#### Document Ingestion
```bash
# Ingest text content
./orchard rag ingest-text "Your text content here"

# Ingest a file
./orchard rag ingest-file /path/to/document.pdf

# List available models
./orchard rag models

# Pull a model from Ollama
./orchard rag pull-model llama3.1:8b
```

### CLI Features

- **Color-coded output**: ✅ success, ❌ error, ⚠️ warning, ℹ️ info
- **Interactive prompts**: Source selection, confirmations
- **Formatted tables**: Clean display of lists and data
- **Progress monitoring**: Real-time job status updates
- **Flexible API connection**: Use `--api-url` to connect to different endpoints

### Example CLI Workflow

```bash
# 1. Check system health
./orchard health

# 2. View current data in the system
./orchard rag info

# 3. List available plugins
./orchard plugins list

# 4. Trigger GitHub repository ingestion
./orchard plugins ingest github
# The CLI will interactively ask you to select a source

# 5. Query the ingested data
./orchard rag query "What are the main features of this repository?"
```

## Usage Examples

### Using the Web Interface

1. **Start the application:**
   ```bash
   ./dev.sh dev  # Development mode
   # OR
   ./start.sh    # Production mode
   ```

2. **Open your browser** and go to `http://localhost:3000`

3. **Upload documents** using the sidebar upload area

4. **Ask questions** in the chat interface

### Using the API Directly

#### 1. Ingest a Document

```bash
curl -X POST "http://localhost:8011/ingest/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text_content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+. It is based on standard Python type hints and provides automatic API documentation.",
    "metadata": {"source": "fastapi_docs", "category": "documentation"}
  }'
```

#### 2. Query the Knowledge Base

```bash
curl -X POST "http://localhost:8011/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is FastAPI?",
    "max_chunks": 3
  }'
```

#### 3. Upload a File

```bash
curl -X POST "http://localhost:8011/ingest" \
  -F "file=@document.pdf" \
  -F "metadata={\"category\": \"technical_docs\"}"
```

#### 4. Check System Health

```bash
curl -X GET "http://localhost:8011/health"
```

## Development

### Project Structure

```
orchard/
├── app/                     # Backend application
│   ├── api/
│   │   └── main.py          # FastAPI application
│   ├── core/
│   │   └── config.py        # Configuration management
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── llm_service.py   # ollama integration
│   │   └── rag_service.py   # RAG workflow
│   └── utils/
│       ├── database.py      # ChromaDB utilities
│       └── document_processor.py  # Document processing
├── cli/                     # Command Line Interface
│   ├── commands/            # CLI command modules
│   │   ├── plugins.py       # Plugin management commands
│   │   └── rag.py          # RAG system commands
│   ├── helpers.py           # Helper utilities
│   ├── main.py             # CLI entry point
│   └── README.md           # CLI documentation
├── frontend/                # React frontend (TypeScript)
│   ├── src/
│   │   ├── components/      # React components (TypeScript)
│   │   ├── services/        # API services (TypeScript)
│   │   ├── types/           # TypeScript type definitions
│   │   ├── styles/          # CSS files
│   │   └── App.tsx          # Main App component
│   ├── public/              # Public assets
│   ├── package.json         # Frontend dependencies
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   ├── postcss.config.js    # PostCSS configuration
│   ├── tsconfig.json        # TypeScript configuration
│   ├── Dockerfile          # Production frontend Docker config
│   └── Dockerfile.dev      # Development frontend Docker config
├── main.py                  # Backend entry point
├── orchard                  # CLI wrapper script
├── orchard_cli.py           # CLI entry point
├── orchard_cli_standalone.py # Standalone CLI (no dependencies)
├── requirements.txt         # Python dependencies
├── docker-compose.yml      # Production Docker setup
├── docker-compose.dev.yml  # Development Docker setup
├── dev.sh                  # Development workflow script
├── start.sh                # Production startup script
├── setup_ollama.py         # Ollama setup script
└── README.md               # This file
```

### Development Workflow

1. **Start development environment:**
   ```bash
   ./dev.sh dev
   ```

2. **Make changes to code:**
   - Backend changes in `app/` directory automatically restart the server
   - Frontend changes in `frontend/src/` automatically reload the browser
   - Tailwind CSS classes are automatically compiled

3. **View logs:**
   ```bash
   ./dev.sh logs
   ```

4. **Stop development environment:**
   ```bash
   ./dev.sh stop
   ```

5. **Clean rebuild:**
   ```bash
   ./dev.sh rebuild
   ```

### Frontend Development

The frontend uses modern technologies:

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **PostCSS** for CSS processing
- **Hot Module Replacement** for instant updates
- **ESLint** for code quality

### Backend Development

The backend includes:

- **FastAPI** with automatic OpenAPI documentation
- **Uvicorn** with hot reloading in development
- **Pydantic** for data validation
- **ChromaDB** for vector storage
- **Ollama** integration for AI responses

### Running Tests

```bash
# Test system components
curl -X GET "http://localhost:8011/test"

# Test document ingestion
curl -X POST "http://localhost:8011/ingest/text" \
  -H "Content-Type: application/json" \
  -d '{"text_content": "Test document content"}'

# Test query
curl -X POST "http://localhost:8011/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is in the test document?"}'
```

## Supported File Formats

- **PDF**: `.pdf` files
- **Word Documents**: `.docx`, `.doc` files
- **Text Files**: `.txt` files
- **Raw Text**: Direct text input via API

## API Documentation

Once the application is running, you can access:

- **Interactive API Docs**: `http://localhost:8011/docs`
- **ReDoc Documentation**: `http://localhost:8011/redoc`

## Troubleshooting

### Common Issues

1. **Ollama Connection Error**
   - Ensure Ollama is installed and running: `ollama serve`
   - Check that the `OLLAMA_HOST` is correctly configured
   - Verify the model is available: `ollama list`

2. **Model Not Found Error**
   - Pull the required model: `ollama pull llama3.1:8b`
   - Or use a different model that's available locally

3. **ChromaDB Initialization Error**
   - Check that the `CHROMA_DB_PATH` directory is writable
   - Ensure sufficient disk space for embedding storage

4. **File Upload Error**
   - Verify file format is supported (PDF, DOCX, TXT)
   - Check file size limits and permissions

5. **Docker Issues**
   - Ensure Docker and Docker Compose are installed
   - Check that ports 3000 and 8011 are available
   - For Docker: Ensure Ollama is accessible via `host.docker.internal:11434`

6. **Port 3000 Already in Use**
   - Stop existing processes: `./dev.sh stop`
   - Kill React dev servers: `pkill -f "node.*react-scripts"`
   - Or use the cleanup command: `./dev.sh cleanup`

7. **Tailwind CSS Not Working**
   - Ensure the development environment is properly started with `./dev.sh dev`
   - Check that `tailwind.config.js` and `postcss.config.js` are properly configured
   - Verify that `src/index.css` contains the Tailwind directives

### Development Troubleshooting

```bash
# Check container status
docker-compose -f docker-compose.dev.yml ps

# View logs
./dev.sh logs

# Clean restart
./dev.sh rebuild

# Manual cleanup
./dev.sh cleanup
```

### Logs

Check application logs:
```bash
# Development logs
./dev.sh logs

# Production logs
docker-compose logs

# Specific service logs
docker-compose -f docker-compose.dev.yml logs frontend
docker-compose -f docker-compose.dev.yml logs api
```

## Performance Optimization

- **Chunk Size**: Adjust `CHUNK_SIZE` based on your documents
- **Embedding Model**: Use different models for speed vs. accuracy tradeoffs
- **Retrieved Chunks**: Balance `MAX_RETRIEVED_CHUNKS` for context vs. speed
- **Temperature**: Lower values for more consistent responses

## Security Considerations

- Store API keys securely using environment variables
- Implement authentication for production deployments
- Validate and sanitize file uploads
- Use HTTPS in production environments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Start development environment: `./dev.sh dev`
4. Make your changes
5. Add tests if applicable
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the API documentation at `/docs`
- Create an issue in the repository

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [React](https://reactjs.org/) and [TypeScript](https://www.typescriptlang.org/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Vector storage powered by [ChromaDB](https://www.trychroma.com/)
- Document processing using [LangChain](https://langchain.com/)
- Embeddings via [SentenceTransformers](https://www.sbert.net/)
- Local AI responses from [Ollama](https://ollama.com/)



