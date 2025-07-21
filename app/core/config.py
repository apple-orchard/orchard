from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Import prompt config manager
from app.core.prompt_config import prompt_config

class Settings(BaseSettings):
    # Ollama Configuration
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    
    # ChromaDB Configuration
    chroma_db_path: str = "./chroma_db"
    
    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Text Processing Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # LLM Configuration
    max_tokens: int = 500
    temperature: float = 0.7
    max_retrieved_chunks: int = 5
    
    @property
    def system_prompt(self) -> str:
        """Get system prompt from persistent config."""
        return prompt_config.get_system_prompt()
    
    @system_prompt.setter
    def system_prompt(self, value: str):
        """Set system prompt in persistent config."""
        prompt_config.set_system_prompt(value)
    
    # API Configuration
    api_title: str = "RAG API"
    api_description: str = "A FastAPI-based RAG system with ChromaDB"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings() 