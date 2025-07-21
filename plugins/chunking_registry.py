"""Registry for document chunking plugins."""

import logging
from typing import Dict, Any, Optional, Protocol, List
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)


class ChunkingPlugin(Protocol):
    """Protocol for chunking plugins."""
    
    def can_process(self, file_path: str) -> bool:
        """Check if this plugin can process the file."""
        ...
    
    def process_file(self, file_path: str, additional_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process a file and return chunks."""
        ...


class ChunkingRegistry:
    """Registry for managing chunking plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, ChunkingPlugin] = {}
        self._priorities: Dict[str, int] = {}
        self._load_plugins()
    
    def _load_plugins(self):
        """Load available chunking plugins."""
        logger.info("Loading chunking plugins...")
        
        # Try to load PyMuPDF4LLM plugin
        try:
            from plugins.pymupdf4llm import PyMuPDF4LLMProcessor
            from plugins.pymupdf4llm.config import PyMuPDF4LLMConfig
            
            # Load config from settings if available
            config = PyMuPDF4LLMConfig()
            processor = PyMuPDF4LLMProcessor(config)
            
            self.register_plugin("pymupdf4llm", processor, priority=10)
            logger.info("Successfully loaded PyMuPDF4LLM plugin")
        except ImportError as e:
            logger.warning(f"PyMuPDF4LLM plugin not available: {e}")
        
        # Try to load Markdown plugin
        try:
            from plugins.markdown import MarkdownChunkingPlugin
            
            markdown_plugin = MarkdownChunkingPlugin()
            self.register_plugin("markdown", markdown_plugin, priority=15)
            logger.info("Successfully loaded Markdown plugin")
        except ImportError as e:
            logger.warning(f"Markdown plugin not available: {e}")
        
        # Try to load Code plugin
        try:
            from plugins.code import CodeChunkingPlugin
            
            code_plugin = CodeChunkingPlugin()
            self.register_plugin("code", code_plugin, priority=20)
            logger.info("Successfully loaded Code plugin")
        except ImportError as e:
            logger.warning(f"Code plugin not available: {e}")
    
    def register_plugin(self, name: str, plugin: ChunkingPlugin, priority: int = 0):
        """Register a chunking plugin.
        
        Args:
            name: Plugin name
            plugin: Plugin instance
            priority: Higher priority plugins are tried first
        """
        self._plugins[name] = plugin
        self._priorities[name] = priority
    
    def get_plugin_for_file(self, file_path: str) -> Optional[ChunkingPlugin]:
        """Get the best plugin for processing a file."""
        logger.debug(f"Finding best plugin for file: {file_path}")
        
        # Sort plugins by priority (highest first)
        sorted_plugins = sorted(
            self._plugins.items(),
            key=lambda x: self._priorities[x[0]],
            reverse=True
        )
        
        # Find first plugin that can handle the file
        for name, plugin in sorted_plugins:
            if plugin.can_process(file_path):
                logger.info(f"Selected plugin '{name}' for file: {file_path}")
                return plugin
        
        logger.debug(f"No suitable plugin found for file: {file_path}")
        return None
    
    def process_file_with_best_plugin(
        self,
        file_path: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Process a file with the best available plugin."""
        plugin = self.get_plugin_for_file(file_path)
        if plugin:
            return plugin.process_file(file_path, additional_metadata)
        return None
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins."""
        return [
            {
                "name": name,
                "priority": self._priorities[name],
                "type": type(plugin).__name__
            }
            for name, plugin in self._plugins.items()
        ]


# Global registry instance
chunking_registry = ChunkingRegistry() 