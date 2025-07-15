"""Plugin configuration management."""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional


class PluginConfigManager:
    """Manages plugin configurations from rag_config.jsonc."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("rag_config.jsonc")
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _strip_jsonc_comments(self, text: str) -> str:
        """Remove comments from JSONC text."""
        # Remove single-line comments
        text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
        # Remove multi-line comments
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Remove trailing commas
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        return text
    
    def _load_config(self) -> None:
        """Load configuration from the JSONC file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    content = f.read()
                    # Strip comments and parse as regular JSON
                    cleaned_content = self._strip_jsonc_comments(content)
                    self._config = json.loads(cleaned_content)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}")
                self._config = self._get_default_config()
        else:
            print(f"Config file {self.config_path} not found. Using default configuration.")
            self._config = self._get_default_config()
            self._save_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure."""
        return {
            "version": "1.0",
            "plugins": {
                "github": {
                    "enabled": False,
                    "config": {
                        "repositories": [],
                        "github_token": "${GITHUB_TOKEN}"
                    }
                },
                "website": {
                    "enabled": False,
                    "config": {
                        "sites": [],
                        "crawler_settings": {
                            "max_depth": 2,
                            "respect_robots_txt": True,
                            "user_agent": "OrchardRAG/1.0"
                        }
                    }
                }
            },
            "global_settings": {
                "chunk_size": 1024,
                "chunk_overlap": 200,
                "batch_size": 100,
                "auto_sync": False,
                "sync_interval_hours": 24
            }
        }
    
    def _save_config(self) -> None:
        """Save configuration to the JSONC file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config to {self.config_path}: {e}")
    
    def _interpolate_env_vars(self, value: Any) -> Any:
        """Interpolate environment variables in configuration values.
        
        Args:
            value: Configuration value that may contain ${VAR_NAME}
            
        Returns:
            Value with environment variables interpolated
        """
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            return os.environ.get(var_name, value)
        elif isinstance(value, dict):
            return {k: self._interpolate_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._interpolate_env_vars(item) for item in value]
        return value
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration with environment variables interpolated
        """
        plugin_config = self._config.get("plugins", {}).get(plugin_name, {})
        return self._interpolate_env_vars(plugin_config)
    
    def update_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Update configuration for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            config: New configuration
        """
        if "plugins" not in self._config:
            self._config["plugins"] = {}
        
        self._config["plugins"][plugin_name] = config
        self._save_config()
    
    def get_global_settings(self) -> Dict[str, Any]:
        """Get global settings.
        
        Returns:
            Global settings dictionary
        """
        return self._config.get("global_settings", {})
    
    def update_global_settings(self, settings: Dict[str, Any]) -> None:
        """Update global settings.
        
        Args:
            settings: New global settings
        """
        self._config["global_settings"] = settings
        self._save_config()
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if plugin is enabled, False otherwise
        """
        plugin_config = self._config.get("plugins", {}).get(plugin_name, {})
        return plugin_config.get("enabled", False)
    
    def enable_plugin(self, plugin_name: str) -> None:
        """Enable a plugin.
        
        Args:
            plugin_name: Name of the plugin
        """
        if "plugins" not in self._config:
            self._config["plugins"] = {}
        if plugin_name not in self._config["plugins"]:
            self._config["plugins"][plugin_name] = {}
        
        self._config["plugins"][plugin_name]["enabled"] = True
        self._save_config()
    
    def disable_plugin(self, plugin_name: str) -> None:
        """Disable a plugin.
        
        Args:
            plugin_name: Name of the plugin
        """
        if "plugins" in self._config and plugin_name in self._config["plugins"]:
            self._config["plugins"][plugin_name]["enabled"] = False
            self._save_config()
    
    def get_full_config(self) -> Dict[str, Any]:
        """Get the full configuration.
        
        Returns:
            Full configuration dictionary
        """
        return self._interpolate_env_vars(self._config)


# Global config manager instance
plugin_config_manager = PluginConfigManager() 