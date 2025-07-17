"""
Intent detection service for routing user queries to appropriate plugins.
"""

import re
from typing import Optional, Dict, Any
from enum import Enum


class Intent(str, Enum):
    """Available intents that can be detected."""
    ECHO = "echo"
    RAG_QUERY = "rag_query"
    UNKNOWN = "unknown"


class IntentDetectionService:
    """Service for detecting user intent from queries."""

    def __init__(self):
        # Define patterns for different intents
        self.intent_patterns = {
            Intent.ECHO: [
                r"echo\s+(.+)",
                r"repeat\s+(.+)",
                r"say\s+(.+)\s+back",
                r"mirror\s+(.+)",
                r"can you echo\s+(.+)",
                r"please echo\s+(.+)",
            ]
        }

    def detect_intent(self, query: str) -> Dict[str, Any]:
        """
        Detect the intent from a user query.

        Args:
            query: The user's input query

        Returns:
            Dictionary containing:
            - intent: The detected intent
            - confidence: Confidence score (0.0 to 1.0)
            - extracted_data: Any extracted data from the query
        """
        query_lower = query.lower().strip()

        # Check for echo intent
        echo_result = self._check_echo_intent(query_lower)
        if echo_result:
            return {
                "intent": Intent.ECHO,
                "confidence": 0.9,
                "extracted_data": echo_result
            }

        # Default to RAG query if no specific intent detected
        return {
            "intent": Intent.RAG_QUERY,
            "confidence": 0.5,
            "extracted_data": {"query": query}
        }

    def _check_echo_intent(self, query: str) -> Optional[Dict[str, str]]:
        """Check if the query matches echo intent patterns."""
        for pattern in self.intent_patterns[Intent.ECHO]:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Extract the text to echo
                text_to_echo = match.group(1).strip()
                return {
                    "text_to_echo": text_to_echo,
                    "original_query": query
                }
        return None


# Global intent detection service
intent_service = IntentDetectionService()