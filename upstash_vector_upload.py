#!/usr/bin/env python3
"""
Standalone script to upload documents to Upstash Vector Database.
Reads files from the documents/ directory and uploads them as vectors with embeddings.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import requests
from datetime import datetime
import time
import hashlib

# Configuration - Set these environment variables
UPSTASH_VECTOR_URL = os.getenv("UPSTASH_VECTOR_URL", "https://innocent-rhino-71555-us1-vector.upstash.io")
UPSTASH_VECTOR_TOKEN = os.getenv("UPSTASH_VECTOR_TOKEN", "ABgFMGlubm9jZW50LXJoaW5vLTcxNTU1LXVzMWFkbWluTWpSaVpETmhOMlV0TnpNME1DMDBOalZsTFRrMFpUZ3RZamxoWTJNeU5ERTRZbU0y")

# Constants
CHUNK_SIZE = 500  # Characters per chunk
BATCH_SIZE = 50   # Vectors to upload in one batch


class UpstashVectorClient:
    """Simple client for Upstash Vector Database."""

    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def upsert(self, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upsert vectors to the database."""
        response = requests.post(
            f"{self.url}/upsert",
            headers=self.headers,
            json={"vectors": vectors}
        )
        response.raise_for_status()
        return response.json()

    def upsert_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upsert text data to the database (Upstash will generate embeddings)."""
        response = requests.post(
            f"{self.url}/upsert-data",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def info(self) -> Dict[str, Any]:
        """Get database info."""
        response = requests.get(f"{self.url}/info", headers=self.headers)
        response.raise_for_status()
        return response.json()



def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Split text into chunks of specified size."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        # Try to break on word boundaries
        if i + chunk_size < len(text):
            last_space = chunk.rfind(' ')
            if last_space > chunk_size * 0.7:  # Only if we don't lose too much
                chunk = chunk[:last_space]
        chunks.append(chunk.strip())

    return [chunk for chunk in chunks if chunk.strip()]


def parse_slack_message(line: str) -> Dict[str, Any]:
    """Parse a single Slack message JSON line."""
    try:
        data = json.loads(line.strip())

        # Convert timestamp to readable format
        ts = float(data.get("ts", 0))
        readable_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "text": data.get("text", ""),
            "user": data.get("user", ""),
            "channel": data.get("channel", ""),
            "timestamp": readable_time,
            "ts": data.get("ts", ""),
            "thread_ts": data.get("thread_ts"),
            "type": data.get("type", "message")
        }
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None


def read_documents(docs_dir: str = "documents") -> List[Dict[str, Any]]:
    """Read all documents from the documents directory."""
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"Documents directory {docs_dir} does not exist")
        return []

    documents = []

    for file_path in docs_path.iterdir():
        if file_path.is_file():
            print(f"Reading {file_path.name}...")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.suffix.lower() == '.txt':
                        if file_path.name.startswith('mock_slack'):
                            # Handle JSON Lines format for Slack messages
                            for line_num, line in enumerate(f, 1):
                                if line.strip():
                                    message = parse_slack_message(line)
                                    if message and message["text"]:
                                        # Create document with metadata
                                        doc = {
                                            "content": message["text"],
                                            "metadata": {
                                                "source": file_path.name,
                                                "line_number": line_num,
                                                "user": message["user"],
                                                "channel": message["channel"],
                                                "timestamp": message["timestamp"],
                                                "ts": message["ts"],
                                                "type": "slack_message"
                                            }
                                        }
                                        if message["thread_ts"]:
                                            doc["metadata"]["thread_ts"] = message["thread_ts"]
                                        documents.append(doc)
                        else:
                            # Handle regular text files
                            content = f.read()
                            documents.append({
                                "content": content,
                                "metadata": {
                                    "source": file_path.name,
                                    "type": "text_file"
                                }
                            })
                    else:
                        # Handle other file types as plain text
                        content = f.read()
                        documents.append({
                            "content": content,
                            "metadata": {
                                "source": file_path.name,
                                "type": "unknown"
                            }
                        })

            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    print(f"Read {len(documents)} documents")
    return documents


def create_vector_id(content: str, metadata: Dict[str, Any]) -> str:
    """Create a unique ID for a vector based on content and metadata."""
    # Create a hash of the content and key metadata
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    source = metadata.get("source", "unknown")
    line_num = metadata.get("line_number", "")
    return f"{source}_{line_num}_{content_hash}" if line_num else f"{source}_{content_hash}"


def process_and_upload(documents: List[Dict[str, Any]],
                      vector_client: UpstashVectorClient):
    """Process documents and upload to Upstash Vector DB."""

    print("Creating text chunks...")
    chunks_data = []

    for doc in documents:
        content = doc["content"]
        metadata = doc["metadata"]

        # Create chunks from the content
        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            chunk_metadata["chunk_length"] = len(chunk)

            chunks_data.append({
                "content": chunk,
                "metadata": chunk_metadata
            })

    print(f"Created {len(chunks_data)} chunks from {len(documents)} documents")

        # Process in batches
    total_uploaded = 0

    for i in range(0, len(chunks_data), BATCH_SIZE):
        batch = chunks_data[i:i + BATCH_SIZE]

        print(f"Processing batch {i//BATCH_SIZE + 1}/{(len(chunks_data) + BATCH_SIZE - 1)//BATCH_SIZE}")

        try:
                        # Prepare data for upload (Upstash will generate embeddings)
            data_items = []
            for chunk_data in batch:
                vector_id = create_vector_id(chunk_data["content"], chunk_data["metadata"])

                # Filter out None values from metadata
                clean_metadata = {k: v for k, v in chunk_data["metadata"].items() if v is not None}

                data_items.append({
                    "id": vector_id,
                    "data": chunk_data["content"],
                    "metadata": clean_metadata
                })

            # Upload to Upstash (embeddings generated automatically)
            print("  Uploading to Upstash...")
            result = vector_client.upsert_data(data_items)

            total_uploaded += len(data_items)
            print(f"  ✅ Uploaded {len(data_items)} data items. Total: {total_uploaded}")

            # Small delay to avoid rate limits
            time.sleep(0.1)

        except Exception as e:
            print(f"  ❌ Error processing batch: {e}, {e.response.text}")
            continue

        print(f"\n🎉 Upload complete! Total data items uploaded: {total_uploaded}")


def main():
    """Main function."""
    # Check environment variables
    if not UPSTASH_VECTOR_URL:
        print("❌ UPSTASH_VECTOR_URL environment variable not set")
        return

    if not UPSTASH_VECTOR_TOKEN:
        print("❌ UPSTASH_VECTOR_TOKEN environment variable not set")
        return

    print("🚀 Starting document upload to Upstash Vector DB")
    print(f"Vector DB URL: {UPSTASH_VECTOR_URL}")
    print(f"Chunk size: {CHUNK_SIZE} characters")
    print(f"Batch size: {BATCH_SIZE} data items")
    print("Embeddings: Generated by Upstash")
    print()

    # Initialize client
    vector_client = UpstashVectorClient(UPSTASH_VECTOR_URL, UPSTASH_VECTOR_TOKEN)

        # Test connections
    try:
        info = vector_client.info()
        print(f"✅ Connected to Upstash Vector DB: {info.get('vectorCount', 0)} existing vectors")
    except Exception as e:
        print(f"❌ Failed to connect to Upstash Vector DB: {e}")
        return

    # Read documents
    documents = read_documents()
    if not documents:
        print("❌ No documents found to process")
        return

    # Process and upload
    process_and_upload(documents, vector_client)


if __name__ == "__main__":
    main()