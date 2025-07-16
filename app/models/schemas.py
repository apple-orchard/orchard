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
class BatchIngestRequest(BaseModel):
    messages: list[dict]
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