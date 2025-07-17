from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Ollama Configuration
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # ChromaDB Configuration
    chroma_db_path: str = "./chroma_db"

    # Embedding Configuration - Better semantic understanding
    # Options for better topic/semantic understanding:
    # - "all-mpnet-base-v2": Best overall semantic similarity (420MB)
    # - "all-MiniLM-L12-v2": Better than L6, good balance (120MB)
    # - "paraphrase-mpnet-base-v2": Excellent for paraphrasing/topics (420MB)
    # - "sentence-t5-base": Good for semantic search (220MB)
    embedding_model: str = "all-mpnet-base-v2"

    # Text Processing Configuration - Optimized for semantic understanding
    chunk_size: int = 1500  # Larger chunks for better topic coherence
    chunk_overlap: int = 300  # More overlap to preserve context across chunks

    # LLM Configuration
    max_tokens: int = 500
    temperature: float = 0.7
    max_retrieved_chunks: int = 5

    # API Configuration
    api_title: str = "RAG API"
    api_description: str = "A FastAPI-based RAG system with ChromaDB"
    api_version: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()