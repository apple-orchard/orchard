"""LlamaIndex client configuration and initialization."""

from typing import Optional
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from app.core.config import settings
from app.utils.database import chroma_db


_llama_index_client: Optional[VectorStoreIndex] = None


def get_llama_index_client() -> VectorStoreIndex:
    """Get or create a LlamaIndex client with ChromaDB integration.

    Returns:
        VectorStoreIndex instance configured with ChromaDB
    """
    global _llama_index_client

    if _llama_index_client is None:
        # Use the shared ChromaDB client from app.utils.database
        chroma_client = chroma_db.get_client()

        # Get or create collection using the shared manager
        collection = chroma_db.get_or_create_collection(
            name=getattr(settings, 'chroma_collection_name', 'llamaindex'),
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