from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import http_exception_handler
from typing import Optional
import tempfile
import os
from datetime import datetime
from fastapi.exception_handlers import http_exception_handler
from app.core.config import settings
from app.models.schemas import (
    QueryRequest, QueryResponse, IngestRequest, IngestResponse,
    HealthResponse, BatchIngestRequest, BatchIngestResponse
)
from app.services.rag_service import rag_service
from app.services.plugin_service import plugin_service
from app.api.plugins import router as plugins_router
from app.services.intent_detection import intent_service, Intent
from app.services.streaming_plugin_handler import StreamingPluginHandler
from io import StringIO
import json
from app.core.logging import logger
from app.agents.query_agent import QueryAgentFactory
from app.agents.qa_agent import QAAgentFactory
from app.core.context_providers import RAGContextProvider

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(plugins_router, prefix="/api")

# Initialize agents
query_agent = QueryAgentFactory.build()
qa_agent = QAAgentFactory.build()

@app.exception_handler(HTTPException)
async def global_exception_handler(request, exc: HTTPException):
    if exc.status_code >= 500:
        logger.exception(f"Unhandled exception for request {request.url.path}")

    return await http_exception_handler(request, exc)

# Initialize plugin service on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    plugin_service.initialize()
    logger.info("Plugin service initialized")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.api_version
    )

@app.post("/query")
async def query_documents(request: QueryRequest, http_request: Request):
    """
    Query the knowledge base with a question.

    This endpoint accepts a question and returns an AI-generated answer
    based on relevant documents in the knowledge base. It also handles
    special intents like echo requests.
    based on relevant documents in the knowledge base.

    Supports different response formats based on Accept header:
    - text/plain: Returns just the answer as plain text
    - application/stream+json: Returns streaming JSON response
    - application/json: Returns complete JSON response with sources and metadata
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        # Detect intent from the query
        intent_result = intent_service.detect_intent(request.question)

        # Handle echo intent with streaming plugin
        if intent_result["intent"] == Intent.ECHO:
            text_to_echo = intent_result["extracted_data"]["text_to_echo"]

            # Use streaming echo plugin
            handler = StreamingPluginHandler("streaming_echo")
            input_stream = StringIO(text_to_echo)
            output_stream = StringIO()

            header = {
                "type": "text",
                "action": "echo",
                "timestamp": str(datetime.now())
            }

            try:
                handler.stream(header, input_stream, output_stream)
                echoed_text = output_stream.getvalue()

                return QueryResponse(
                    answer=f"Echo: {echoed_text}",
                    sources=[],
                    metadata={
                        "intent": "echo",
                        "plugin_used": "streaming_echo",
                        "original_query": request.question
                    }
                )
            except Exception as e:
                logger.exception("Error running streaming echo plugin")
                # Fallback to simple echo
                return QueryResponse(
                    answer=f"Echo (fallback): {text_to_echo}",
                    sources=[],
                    metadata={
                        "intent": "echo",
                        "plugin_used": "fallback",
                        "error": str(e)
                    }
                )

        # Get the Accept header
        accept_header = http_request.headers.get("accept", "application/json")

        # Process the query using RAG service
        stream = rag_service.query(
            question=request.question,
            query_agent=query_agent,
            qa_agent=qa_agent,
            max_chunks=request.max_chunks,
        )

        # Handle text/plain response
        if "text/plain" in accept_header:
            final_answer = ""
            async for chunk in stream:
                if "done" in chunk:
                    break
                if "answer" in chunk:
                    final_answer = chunk["answer"]
            return PlainTextResponse(content=final_answer)

        if "text/stream+plain" in accept_header:
            async def generate_text_stream():
                current_answer = ""
                async for chunk in stream:
                    if "done" in chunk:
                        break
                    if "answer" in chunk and chunk["answer"] != current_answer:
                        if current_answer == "":
                            current_answer = chunk["answer"]
                            yield current_answer
                        else:
                            new_token = str(chunk["answer"]).split(sep=current_answer)[-1]
                            current_answer += new_token or current_answer
                            yield new_token

            return StreamingResponse(
                generate_text_stream(),
                media_type="text/stream+plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )

        # Handle application/stream+json response
        elif "application/stream+json" in accept_header:
            async def generate_json_stream():
                async for chunk in stream:
                    if "done" in chunk:
                        yield f"data: {json.dumps({'done': True})}\n\n"
                    else:
                        yield f"data: {json.dumps(chunk)}\n\n"

            return StreamingResponse(
                generate_json_stream(),
                media_type="application/stream+json",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )

        # Handle application/json response (default)
        else:
            # Consume all chunks from the generator to get the complete response
            final_answer = ""
            sources = None
            metadata = None

            async for chunk in stream:
                if "done" in chunk:
                    break
                if "answer" in chunk:
                    final_answer = chunk["answer"]
                if "sources" in chunk and sources is None:
                    sources = chunk["sources"]
                if "usage" in chunk and metadata is None:
                    metadata = chunk.get("usage", {})

            return QueryResponse(
                answer=final_answer,
                sources=sources,
                metadata=metadata
            )

    except ValueError as e:
        logger.exception("ValueError in query processing")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Exception in query processing")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: Optional[UploadFile] = File(None),
    text_content: Optional[str] = Form(None),
    file_path: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """
    Ingest a document into the knowledge base.

    You can provide either:
    - A file upload
    - Raw text content
    - A file path (for server-side files)

    Optional metadata can be provided as a JSON string.
    """
    try:
        # Parse metadata if provided
        additional_metadata = {}
        if metadata:
            import json
            try:
                additional_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in metadata field")

        # Process file upload
        if file:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name

            try:
                # Process the uploaded file
                result = rag_service.ingest_file(tmp_file_path, additional_metadata)
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)

        # Process text content
        elif text_content:
            result = rag_service.ingest_text(text_content, additional_metadata)

        # Process file path
        elif file_path:
            if not os.path.exists(file_path):
                raise HTTPException(status_code=400, detail=f"File not found: {file_path}")

            # Check if it's a directory
            if os.path.isdir(file_path):
                result = rag_service.ingest_directory(file_path, True, additional_metadata)
            else:
                result = rag_service.ingest_file(file_path, additional_metadata)

        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either file upload, text_content, or file_path"
            )

        return IngestResponse(
            success=result["success"],
            message=result["message"],
            chunks_created=result["chunks_created"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/ingest/batch", response_model=BatchIngestResponse)
async def ingest_batch_messages(request: BatchIngestRequest):
    """
    Endpoint to ingest a batch of messages (e.g., Slack messages) into the knowledge base.
    Each message should be a dict with at least a 'text' field.
    """
    try:
        total_chunks = 0
        errors = []
        for idx, msg in enumerate(request.messages):
            text = msg.text
            if not text:
                errors.append(f"Message at index {idx} missing 'text' field.")
                continue
            # Merge message metadata and request metadata for traceability
            if request.metadata is not None and not isinstance(request.metadata, dict):
                raise HTTPException(status_code=400, detail="Invalid type for metadata. Expected a dictionary.")
            metadata = dict(request.metadata) if request.metadata else {}
            if msg.metadata:
                if not isinstance(msg.metadata, dict):
                    raise HTTPException(status_code=400, detail=f"Invalid type for message metadata at index {idx}. Expected a dictionary.")
                metadata.update(msg.metadata)
            result = rag_service.ingest_text(text, metadata)
            if result.get("success"):
                total_chunks += result.get("chunks_created", 0)
            else:
                errors.append(f"Error ingesting message at index {idx}: {result.get('message')}")
        success = len(errors) == 0
        message = "Batch ingestion completed successfully." if success else f"Completed with errors: {'; '.join(errors)}"
        return BatchIngestResponse(
            success=success,
            message=message,
            total_chunks_created=total_chunks
        )
    except HTTPException:
        raise
    except Exception as e:
        return BatchIngestResponse(
            success=False,
            message=f"Internal server error: {str(e)}",
            total_chunks_created=0
        )

@app.get("/knowledge-base/info")
async def get_knowledge_base_info():
    """Get information about the knowledge base"""
    try:
        info = rag_service.get_knowledge_base_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/test")
async def test_system():
    """Test all components of the RAG system"""
    try:
        results = rag_service.test_system()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/reload-config")
async def reload_configuration():
    """Reload configuration from file"""
    try:
        # Reinitialize plugin service to reload configuration
        plugin_service.initialize()
        return {"message": "Configuration reloaded successfully", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload configuration: {str(e)}")

@app.post("/ingest/text", response_model=IngestResponse)
async def ingest_text_simple(request: IngestRequest):
    """
    Simple endpoint to ingest text content.

    This is a simplified version of the /ingest endpoint for text-only ingestion.
    """
    try:
        if not request.text_content:
            raise HTTPException(status_code=400, detail="text_content is required")

        result = rag_service.ingest_text(request.text_content, request.metadata)

        return IngestResponse(
            success=result["success"],
            message=result["message"],
            chunks_created=result["chunks_created"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/ingest/file", response_model=IngestResponse)
async def ingest_file_simple(request: IngestRequest):
    """
    Simple endpoint to ingest a file by path.

    This is a simplified version of the /ingest endpoint for file path ingestion.
    """
    try:
        if not request.file_path:
            raise HTTPException(status_code=400, detail="file_path is required")

        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=400, detail=f"File not found: {request.file_path}")

        # Check if it's a directory
        if os.path.isdir(request.file_path):
            result = rag_service.ingest_directory(request.file_path, True, request.metadata)
        else:
            result = rag_service.ingest_file(request.file_path, request.metadata)

        return IngestResponse(
            success=result["success"],
            message=result["message"],
            chunks_created=result["chunks_created"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )
