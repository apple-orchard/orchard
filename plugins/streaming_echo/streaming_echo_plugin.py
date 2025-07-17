import sys
import os
# Add the parent directory (plugins) to the path so we can import streaming_base
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from streaming_base import StreamingPluginBase

class StreamingEchoPlugin(StreamingPluginBase):
    def process_stream(self):
        # Echo raw data from stdin to stdout
        while True:
            chunk = sys.stdin.buffer.read(4096)
            if not chunk:
                break
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()

if __name__ == "__main__":
    StreamingEchoPlugin().run()