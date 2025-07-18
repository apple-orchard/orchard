"""Plugin registry for discovering and managing plugins."""

import importlib
import os
import app.core.logging
from typing import Dict, Optional, List, Type
from pathlib import Path
from .base import IngestionPlugin

logger = app.core.logging.logger.getChild('plugins.registry')
class PluginRegistry:
    """Registry for managing ingestion plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, Type[IngestionPlugin]] = {}
        self._instances: Dict[str, IngestionPlugin] = {}
        self._plugin_dir = Path(__file__).parent
    
    def discover_plugins(self) -> None:
        """Discover all available plugins in the plugins directory."""
        # Get all subdirectories in the plugins folder
        for item in self._plugin_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_') and item.name not in ['llamaindex']:
                # Check if it has a plugin.py file
                plugin_file = item / "plugin.py"
                if plugin_file.exists():
                    self._load_plugin(item.name)
    
    def _load_plugin(self, plugin_name: str) -> None:
        """Load a specific plugin by name.
        
        Args:
            plugin_name: Name of the plugin directory
        """
        try:
            # Import the plugin module
            module_name = f"plugins.{plugin_name}.plugin"
            module = importlib.import_module(module_name)
            
            # Find the plugin class (should be named <PluginName>IngestionPlugin)
            plugin_class_name = f"{plugin_name.title().replace('_', '')}IngestionPlugin"
            
            if hasattr(module, plugin_class_name):
                plugin_class = getattr(module, plugin_class_name)
                
                # Verify it's a subclass of IngestionPlugin
                if issubclass(plugin_class, IngestionPlugin):
                    self._plugins[plugin_name] = plugin_class
                    logger.info(f"Loaded plugin: {plugin_name}")
                else:
                    logger.warning(f"{plugin_class_name} is not a subclass of IngestionPlugin")
            else:
                logger.warning(f"Could not find {plugin_class_name} in {module_name}")
                
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
    
    def register_plugin(self, name: str, plugin_class: Type[IngestionPlugin]) -> None:
        """Manually register a plugin.
        
        Args:
            name: Name to register the plugin under
            plugin_class: Plugin class (must be subclass of IngestionPlugin)
        """
        if not issubclass(plugin_class, IngestionPlugin):
            raise ValueError(f"{plugin_class} must be a subclass of IngestionPlugin")
        
        self._plugins[name] = plugin_class
    
    def get_plugin_class(self, name: str) -> Optional[Type[IngestionPlugin]]:
        """Get a plugin class by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin class or None if not found
        """
        return self._plugins.get(name)
    
    def create_instance(self, name: str, config: Dict) -> Optional[IngestionPlugin]:
        """Create an instance of a plugin.
        
        Args:
            name: Plugin name
            config: Plugin configuration
            
        Returns:
            Plugin instance or None if plugin not found
        """
        plugin_class = self._plugins.get(name)
        if plugin_class:
            instance = plugin_class(name, config)
            self._instances[name] = instance
            return instance
        return None
    
    def get_instance(self, name: str) -> Optional[IngestionPlugin]:
        """Get an existing plugin instance.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None if not found
        """
        return self._instances.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugins.
        
        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())
    
    def get_plugin_info(self, name: str) -> Optional[Dict]:
        """Get information about a specific plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin information or None if not found
        """
        instance = self._instances.get(name)
        if instance:
            return instance.get_plugin_info()
        
        # Try to create a temporary instance to get info
        plugin_class = self._plugins.get(name)
        if plugin_class:
            try:
                temp_instance = plugin_class(name, {})
                return temp_instance.get_plugin_info()
            except:
                pass
        
        return None


# Global registry instance
plugin_registry = PluginRegistry() 