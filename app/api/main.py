from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import tempfile
import os
from datetime import datetime

from app.core.config import settings
from app.models.schemas import (
    QueryRequest, QueryResponse, IngestRequest, IngestResponse, 
    HealthResponse
)
from app.services.rag_service import rag_service
from app.services.plugin_service import plugin_service
from app.api.plugins import router as plugins_router

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

# Initialize plugin service on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    plugin_service.initialize()
    print("Plugin service initialized")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.api_version
    )

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query the knowledge base with a question.
    
    This endpoint accepts a question and returns an AI-generated answer
    based on relevant documents in the knowledge base.
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Process the query using RAG service
        result = rag_service.query(
            question=request.question,
            max_chunks=request.max_chunks
        )
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            metadata=result["metadata"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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

@app.get("/models")
async def list_models():
    """List available Ollama models"""
    try:
        from app.services.llm_service import llm_service
        models = llm_service.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/models/pull")
async def pull_model(model_name: str):
    """Pull a model from Ollama"""
    try:
        from app.services.llm_service import llm_service
        success = llm_service.pull_model(model_name)
        if success:
            return {"message": f"Model {model_name} pulled successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to pull model {model_name}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011) 