"""Embedding model configuration for LlamaIndex."""

from typing import Optional
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from app.core.config import settings


_embedding_model: Optional[HuggingFaceEmbedding] = None


def get_embedding_model() -> HuggingFaceEmbedding:
    """Get or create the embedding model compatible with existing setup.

    Returns:
        HuggingFaceEmbedding instance
    """
    global _embedding_model

    if _embedding_model is None:
        # Use the same model as the existing setup
        # Default is 'all-mpnet-base-v2' which provides better semantic understanding
        model_name = getattr(settings, 'embedding_model_name', f'sentence-transformers/{settings.embedding_model}')

        # Use environment cache folder if available
        import os
        cache_folder = os.environ.get('SENTENCE_TRANSFORMERS_HOME', getattr(settings, 'model_cache_dir', None))

        _embedding_model = HuggingFaceEmbedding(
            model_name=model_name,
            cache_folder=cache_folder,
            device='cpu'  # Can be changed to 'cuda' if GPU is available
        )

    return _embedding_model


def reset_embedding_model() -> None:
    """Reset the embedding model (useful for testing)."""
    global _embedding_model
    _embedding_model = None