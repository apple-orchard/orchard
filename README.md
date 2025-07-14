# RAG API - Retrieval-Augmented Generation with FastAPI

A full-stack RAG (Retrieval-Augmented Generation) system with a Python backend and React frontend. The backend uses FastAPI, ChromaDB, and Ollama for document processing and AI-powered question answering. The frontend provides a simple chat interface for interacting with your documents.

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

### Frontend Features
- **Chat Interface**: Simple, intuitive chat interface for document Q&A
- **Document Upload**: Drag-and-drop file upload with progress indicators
- **Real-time Responses**: Live chat with typing indicators and timestamps
- **Source Display**: Shows document sources for each answer
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: User-friendly error messages and retry options
- **Docker Support**: Containerized deployment with the backend

## Requirements

- Python 3.11+
- Ollama installed and running locally
- Docker (optional, for containerized deployment)

## Installation

### Option 1: Local Development

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

3. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your Ollama configuration if needed
```

6. **Run the backend:**
```bash
python main.py
```

7. **Run the frontend (in a new terminal):**
```bash
cd frontend
npm install
npm start
```

The application will be available at:
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8011`

### Quick Setup

You can also use the automated setup script to check your Ollama installation:

```bash
python setup_ollama.py
```

This script will:
- Check if Ollama is installed and running
- List available models
- Pull the recommended model if needed
- Test the model connection

### Option 2: Docker Deployment

1. **Install and start Ollama on host:**
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

3. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your Ollama configuration if needed
```

4. **Run with Docker Compose:**
```bash
# Quick start (recommended)
./start.sh

# Or manually
docker-compose up -d
```

The application will be available at:
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8011`
- **API Documentation**: `http://localhost:8011/docs`

### Development Mode

For development with hot reloading:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

This will:
- Mount source code for live reloading
- Enable React development server with hot reloading
- Keep containers running with development optimizations

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

## Usage Examples

### Using the Web Interface

1. **Start the application:**
   ```bash
   docker-compose up -d
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
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   ├── styles/          # CSS files
│   │   └── App.js           # Main App component
│   ├── public/              # Public assets
│   ├── package.json         # Frontend dependencies
│   └── Dockerfile          # Frontend Docker config
├── main.py                  # Backend entry point
├── requirements.txt         # Python dependencies
├── docker-compose.yml      # Production Docker setup
├── docker-compose.dev.yml  # Development Docker setup
├── setup_ollama.py         # Ollama setup script
└── README.md               # This file
```

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

### Logs

Check application logs:
```bash
# Docker logs
docker-compose logs rag-api

# Local development
python main.py  # Logs will appear in console
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
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the API documentation at `/docs`
- Create an issue in the repository

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Vector storage powered by [ChromaDB](https://www.trychroma.com/)
- Document processing using [LangChain](https://langchain.com/)
- Embeddings via [SentenceTransformers](https://www.sbert.net/)
- Local AI responses from [Ollama](https://ollama.com/) 