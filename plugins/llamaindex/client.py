"""LlamaIndex client configuration and initialization."""

from typing import Optional
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from app.core.config import settings


_llama_index_client: Optional[VectorStoreIndex] = None


def get_llama_index_client() -> VectorStoreIndex:
    """Get or create a LlamaIndex client with ChromaDB integration.
    
    Returns:
        VectorStoreIndex instance configured with ChromaDB
    """
    global _llama_index_client
    
    if _llama_index_client is None:
        # Initialize ChromaDB client
        if settings.chroma_persist_directory:
            chroma_client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory
            )
        else:
            chroma_client = chromadb.Client()
        
        # Get or create collection
        try:
            collection = chroma_client.get_collection(
                name=settings.chroma_collection_name
            )
        except:
            collection = chroma_client.create_collection(
                name=settings.chroma_collection_name,
                metadata={"description": "LlamaIndex integrated collection"}
            )
        
        # Create ChromaDB vector store
        vector_store = ChromaVectorStore(
            chroma_collection=collection,
            embed_model=None  # We'll use our own embeddings
        )
        
        # Create storage context
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )
        
        # Create index
        _llama_index_client = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context
        )
    
    return _llama_index_client


def reset_client() -> None:
    """Reset the LlamaIndex client (useful for testing)."""
    global _llama_index_client
    _llama_index_client = None 