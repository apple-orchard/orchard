import subprocess
import json
from typing import Dict, IO
from pathlib import Path

class StreamingPluginHandler:
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.plugin_dir = Path("plugins") / plugin_name
        self.venv_python = (self.plugin_dir / ".venv" / "bin" / "python").resolve()
        # Look for the plugin file in the plugin's own directory
        self.main_py = (self.plugin_dir / f"streaming_{plugin_name}_plugin.py").resolve()

        # Fallback to main.py if the streaming_*_plugin.py doesn't exist
        if not self.main_py.exists():
            self.main_py = (self.plugin_dir / "main.py").resolve()

    def stream(self, header: Dict, input_stream: IO, output_stream: IO):
        if not self.venv_python.exists():
            raise FileNotFoundError(f"Virtual environment not found for plugin {self.plugin_name}. Path {self.venv_python.absolute()} Run: python plugins/plugin_setup.py setup {self.plugin_name}")

        if not self.main_py.exists():
            raise FileNotFoundError(f"Plugin file not found: {self.main_py}")

        proc = subprocess.Popen(
            [str(self.venv_python), str(self.main_py)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=0  # unbuffered
        )
        # Send JSON header
        header_bytes = (json.dumps(header) + "\n").encode()
        proc.stdin.write(header_bytes)
        proc.stdin.flush()
        # Stream input to plugin
        while True:
            chunk = input_stream.read(4096)
            if not chunk:
                break
            proc.stdin.write(chunk)
            proc.stdin.flush()
        proc.stdin.close()
        # Stream output from plugin
        while True:
            out_chunk = proc.stdout.read(4096)
            if not out_chunk:
                break
            output_stream.write(out_chunk)
            output_stream.flush()
        proc.stdout.close()
        proc.wait()