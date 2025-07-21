"""Persistent configuration for system prompts."""

import json
import os
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """Based on the following context, please answer the question. If the context doesn't contain enough information to answer the question, please say so.

Context:
{context}

Question: {question}

Answer:"""


class PromptConfigManager:
    """Manages persistent system prompt configuration."""
    
    def __init__(self, config_path: str = "prompt_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded prompt config from {self.config_path}")
                    return config
            except Exception as e:
                logger.error(f"Error loading prompt config: {e}")
        
        # Return default config
        return {
            "system_prompt": DEFAULT_SYSTEM_PROMPT
        }
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved prompt config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving prompt config: {e}")
            raise
    
    def get_system_prompt(self) -> str:
        """Get the current system prompt."""
        return self.config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
    
    def set_system_prompt(self, prompt: str):
        """Set and save the system prompt."""
        self.config["system_prompt"] = prompt
        self.save_config()


# Global instance
prompt_config = PromptConfigManager() 