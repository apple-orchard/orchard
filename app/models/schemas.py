from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from typing import Union

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
class ChannelInfo(BaseModel):
    id: str
    name: str
    is_private: bool

class Attachment(BaseModel):
    type: str  # file|image|link
    url: str
    filename: str
    title: str

class Reaction(BaseModel):
    emoji: str
    count: int
    users: List[str]

class DocumentContent(BaseModel):
    text: str
    formatted_text: Optional[str] = None
    attachments: Optional[List[Attachment]] = None

class DocumentMetadata(BaseModel):
    timestamp: str  # ISO 8601
    user_id: str
    user_name: str
    thread_ts: Optional[str] = None
    parent_message_id: Optional[str] = None
    reactions: Optional[List[Reaction]] = None
    edited_timestamp: Optional[str] = None  # ISO 8601
    message_type: str  # regular|bot|system

class BatchDocument(BaseModel):
    document_id: str
    document_type: str  # message|thread|file
    channel: ChannelInfo
    content: DocumentContent
    metadata: DocumentMetadata

class BatchMetadata(BaseModel):
    batch_number: int
    is_final_batch: bool

class BatchIngestRequest(BaseModel):
    batch_id: str
    documents: List[BatchDocument]
    batch_metadata: BatchMetadata

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