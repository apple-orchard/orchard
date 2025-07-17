from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class QueryRequest(BaseModel):
    question: str
    max_chunks: Optional[int] = None

class QueryResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

class IngestRequest(BaseModel):
    file_path: Optional[str] = None
    text_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class IngestResponse(BaseModel):
    success: bool
    message: str
    chunks_created: int

# New models for batch ingestion
class Message(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None

class BatchIngestRequest(BaseModel):
    messages: List[Message]
    metadata: Optional[Dict[str, Any]] = None

class BatchIngestResponse(BaseModel):
    success: bool
    message: str
    total_chunks_created: int

class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

# Async job schemas
class AsyncJobResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    created_at: str
    message: str = ""

class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: float
    message: str
    error_message: str = ""
    chunks_created: int
    total_items: int
    processed_items: int
    metadata: Dict[str, Any]

class JobListResponse(BaseModel):
    jobs: List[JobStatusResponse]
    total_count: int

class JobStatsResponse(BaseModel):
    total_jobs: int
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int
    total_chunks_created: int