"""Plugin system for extensible data ingestion."""

from .base import IngestionPlugin
from .registry import PluginRegistry

__all__ = ["IngestionPlugin", "PluginRegistry"] 