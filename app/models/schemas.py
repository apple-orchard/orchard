from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class QueryRequest(BaseModel):
    question: str
    max_chunks: Optional[int] = None
    
class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class IngestRequest(BaseModel):
    file_path: Optional[str] = None
    text_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    use_smart_chunking: bool = True
    
class IngestResponse(BaseModel):
    success: bool
    message: str
    chunks_created: int
    
class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

class SystemPromptRequest(BaseModel):
    system_prompt: str

class SystemPromptResponse(BaseModel):
    system_prompt: str 