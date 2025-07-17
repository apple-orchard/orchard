import sys
import json
from abc import ABC, abstractmethod
from typing import Dict, Any

class StreamingPluginBase(ABC):
    """
    Base class for streaming plugins. Handles stdin/stdout streaming with a JSON header and raw data.
    """
    def __init__(self):
        self.header = None

    def read_header(self):
        """Read a JSON header from stdin (terminated by newline)."""
        line = sys.stdin.readline()
        self.header = json.loads(line)
        return self.header

    @abstractmethod
    def process_stream(self):
        """
        Process the input stream and write to stdout.
        Should be implemented by subclasses.
        """
        pass

    def run(self):
        self.read_header()
        self.process_stream()

# Example usage in a plugin:
# class MyPlugin(StreamingPluginBase):
#     def process_stream(self):
#         # Read from sys.stdin.buffer, write to sys.stdout.buffer
#         pass