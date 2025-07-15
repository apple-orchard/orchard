"""Plugin service for managing ingestion plugins."""

from typing import Dict, Any, List, Optional
from plugins.registry import plugin_registry
from plugins.config import plugin_config_manager
from plugins.base import IngestionPlugin, IngestionJob


class PluginService:
    """Service for managing ingestion plugins."""
    
    def __init__(self):
        """Initialize the plugin service."""
        self.registry = plugin_registry
        self.config_manager = plugin_config_manager
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the plugin system."""
        if self._initialized:
            return
        
        # Discover available plugins
        self.registry.discover_plugins()
        
        # Initialize enabled plugins
        config = self.config_manager.get_full_config()
        plugins_config = config.get("plugins", {})
        
        for plugin_name, plugin_config in plugins_config.items():
            if plugin_config.get("enabled", False):
                try:
                    self.registry.create_instance(plugin_name, plugin_config)
                    print(f"Initialized plugin: {plugin_name}")
                except Exception as e:
                    print(f"Failed to initialize plugin {plugin_name}: {e}")
        
        self._initialized = True
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins with their status.
        
        Returns:
            List of plugin information
        """
        if not self._initialized:
            self.initialize()
        
        plugins = []
        available_plugins = self.registry.list_plugins()
        
        for plugin_name in available_plugins:
            plugin_info = self.registry.get_plugin_info(plugin_name)
            if plugin_info:
                instance = self.registry.get_instance(plugin_name)
                plugin_info["initialized"] = instance is not None
                plugins.append(plugin_info)
        
        return plugins
    
    def get_plugin(self, plugin_name: str) -> Optional[IngestionPlugin]:
        """Get a plugin instance by name.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance or None if not found
        """
        if not self._initialized:
            self.initialize()
        
        return self.registry.get_instance(plugin_name)
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration
        """
        return self.config_manager.get_plugin_config(plugin_name)
    
    def update_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Update configuration for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            config: New configuration
        """
        # Update configuration
        self.config_manager.update_plugin_config(plugin_name, config)
        
        # Reinitialize plugin if it exists
        if self.registry.get_instance(plugin_name):
            try:
                self.registry.create_instance(plugin_name, config)
            except Exception as e:
                print(f"Failed to reinitialize plugin {plugin_name}: {e}")
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config_manager.enable_plugin(plugin_name)
            config = self.config_manager.get_plugin_config(plugin_name)
            self.registry.create_instance(plugin_name, config)
            return True
        except Exception as e:
            print(f"Failed to enable plugin {plugin_name}: {e}")
            return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if successful, False otherwise
        """
        self.config_manager.disable_plugin(plugin_name)
        # Plugin instance will be removed on next initialization
        return True
    
    async def ingest(self, plugin_name: str, source_id: str, full_sync: bool = True) -> str:
        """Trigger ingestion for a specific plugin and source.
        
        Args:
            plugin_name: Name of the plugin
            source_id: Source identifier
            full_sync: Whether to perform full sync
            
        Returns:
            Job ID for tracking progress
            
        Raises:
            ValueError: If plugin not found or not enabled
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not found or not enabled")
        
        return await plugin.ingest(source_id, full_sync)
    
    def get_job_status(self, plugin_name: str, job_id: str) -> Optional[IngestionJob]:
        """Get the status of an ingestion job.
        
        Args:
            plugin_name: Name of the plugin
            job_id: Job identifier
            
        Returns:
            IngestionJob object or None if not found
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return None
        
        return plugin.get_job_status(job_id)
    
    def list_plugin_jobs(self, plugin_name: str) -> List[IngestionJob]:
        """List all jobs for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            List of IngestionJob objects
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return []
        
        return plugin.list_jobs()
    
    async def get_plugin_sources(self, plugin_name: str) -> List[Dict[str, Any]]:
        """Get configured sources for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            List of source configurations
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return []
        
        return await plugin.get_sources()
    
    def get_global_settings(self) -> Dict[str, Any]:
        """Get global plugin settings.
        
        Returns:
            Global settings dictionary
        """
        return self.config_manager.get_global_settings()
    
    def update_global_settings(self, settings: Dict[str, Any]) -> None:
        """Update global plugin settings.
        
        Args:
            settings: New global settings
        """
        self.config_manager.update_global_settings(settings)


# Global plugin service instance
plugin_service = PluginService() 