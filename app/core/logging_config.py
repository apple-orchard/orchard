"""Logging configuration for Orchard RAG system."""

import logging
import sys
from pathlib import Path


def setup_logging(level=logging.INFO):
    """Set up logging configuration for the application."""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with color formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Format with colors for console
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler for persistent logs
    file_handler = logging.FileHandler(logs_dir / "orchard.log")
    file_handler.setLevel(level)
    
    # Detailed format for file
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    # Set specific log levels for modules
    logging.getLogger("plugins.pymupdf4llm").setLevel(logging.INFO)
    logging.getLogger("plugins.chunking_registry").setLevel(logging.INFO)
    logging.getLogger("app.utils.document_processor").setLevel(logging.INFO)
    logging.getLogger("app.services.rag_service").setLevel(logging.INFO)
    logging.getLogger("plugins.llamaindex.converters").setLevel(logging.INFO)
    
    # Reduce noise from third-party libraries
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized") 