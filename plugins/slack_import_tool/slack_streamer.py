#!/usr/bin/env python3
"""
Slack Export Streamer CLI
Processes Slack exported zip files and streams contents to an API
"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Generator
import requests
from datetime import datetime
import time
import uuid
import shutil
import tempfile

class SlackDataProcessor:
    def __init__(self, users: Dict, channels: Dict):
        self.users = users
        self.channels = channels

    def process_message(self, message: Dict, channel_name: str) -> Dict:
        document_id = message.get('client_msg_id') or message.get('ts') or str(uuid.uuid4())
        document_type = 'message'
        if message.get('subtype') == 'thread_broadcast':
            document_type = 'thread'
        elif message.get('files'):
            document_type = 'file'
        channel = {
            "id": message.get('channel', ''),
            "name": channel_name,
            "is_private": message.get('is_private', False)
        }
        content = {
            "text": message.get('text', ''),
            "formatted_text": message.get('formatted_text', ''),
            "attachments": []
        }
        if 'files' in message:
            for f in message['files']:
                content['attachments'].append({
                    "type": f.get('mimetype', '').split('/')[0] if f.get('mimetype') else 'file',
                    "url": f.get('url_private', ''),
                    "filename": f.get('name', ''),
                    "title": f.get('title', '')
                })
        metadata = {
            "timestamp": datetime.fromtimestamp(float(message['ts'])).isoformat() if 'ts' in message else '',
            "user_id": message.get('user', ''),
            "user_name": self.users.get(message.get('user', ''), {}).get('name', ''),
            "thread_ts": message.get('thread_ts', None),
            "parent_message_id": message.get('parent_user_id', None),
            "reactions": [],
            "edited_timestamp": message.get('edited', {}).get('ts') if 'edited' in message else None,
            "message_type": message.get('subtype', 'regular')
        }
        if 'reactions' in message:
            for r in message['reactions']:
                metadata['reactions'].append({
                    "emoji": r.get('name', ''),
                    "count": r.get('count', 0),
                    "users": r.get('users', [])
                })
        doc = {
            "document_id": document_id,
            "document_type": document_type,
            "channel": channel,
            "content": content,
            "metadata": metadata
        }
        return doc

class SlackExportStreamer:
    def __init__(self, api_url: str, api_key: Optional[str] = None, dry_run: bool = False, dry_run_file: str = "dry_run_output.txt"):
        self.api_url = api_url
        self.session = requests.Session()
        self.dry_run = dry_run
        self.dry_run_file = dry_run_file
        
        # Set up authentication if API key provided
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def extract_zip(self, zip_path: str, extract_to: str) -> str:
        """Extract zip file and return extraction path"""
        print(f"Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return extract_to
    
    def load_channels(self, extract_path: str) -> Dict[str, str]:
        """Load channels.json to map channel IDs to names"""
        channels_file = Path(extract_path) / "channels.json"
        if not channels_file.exists():
            return {}
        
        with open(channels_file, 'r', encoding='utf-8') as f:
            channels_data = json.load(f)
        
        return {ch['id']: ch['name'] for ch in channels_data}
    
    def load_users(self, extract_path: str) -> Dict[str, Dict]:
        """Load users.json to map user IDs to user info"""
        users_file = Path(extract_path) / "users.json"
        if not users_file.exists():
            return {}
        
        with open(users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        return {user['id']: user for user in users_data}
    
    def stream_channel_messages(self, extract_path: str, channel_name: str, 
                               users: Dict, batch_size: int = 100) -> Generator[List[Dict], None, None]:
        """Stream messages from a channel directory"""
        channel_path = Path(extract_path) / channel_name
        if not channel_path.exists():
            return
        
        # Get all JSON files in channel directory (daily message files)
        json_files = sorted(channel_path.glob("*.json"))
        
        batch = []
        data_processor = SlackDataProcessor(users, {})
        for json_file in json_files:
            print(f"Processing {json_file.name}...")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                
                for message in messages:
                    processed_message = data_processor.process_message(message, channel_name)
                    batch.append(processed_message)
                    
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                        
            except json.JSONDecodeError as e:
                print(f"Error parsing {json_file}: {e}")
                continue
        
        # Yield remaining messages
        if batch:
            yield batch
    
    def send_to_api(self, data: List[Dict], batch_number: int, is_final_batch: bool) -> bool:
        """Send batch of messages to /ingest/batch API endpoint"""
        url = self.api_url.rstrip('/') + '/ingest/batch'
        filtered_data = [msg for msg in data if 'content' in msg and msg['content'].get('text')]
        if len(filtered_data) < len(data):
            print(f"Warning: {len(data) - len(filtered_data)} messages missing 'text' field were skipped.")
        batch_id = str(uuid.uuid4())
        payload = {
            "batch_id": batch_id,
            "documents": filtered_data,
            "batch_metadata": {
                "batch_number": batch_number,
                "is_final_batch": is_final_batch
            }
        }
        if self.dry_run:
            with open(self.dry_run_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- Batch ---\n")
                f.write(json.dumps(payload, ensure_ascii=False, indent=2))
                f.write("\n")
            print(f"[DRY RUN] Wrote batch of {len(filtered_data)} messages to {self.dry_run_file}")
            return True
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            print(f"Successfully sent batch of {len(filtered_data)} messages to API")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending to API: {e}")
            return False
    
    def process_export(self, zip_path: str, batch_size: int = 100, 
                      delay: float = 0.1) -> None:
        """Main processing function"""
        # Create temporary extraction directory
        extract_path = tempfile.mkdtemp(prefix="slack_export_")
        
        try:
            # Extract zip file
            self.extract_zip(zip_path, extract_path)
            
            # Load metadata
            channels = self.load_channels(extract_path)
            users = self.load_users(extract_path)
            
            print(f"Found {len(channels)} channels and {len(users)} users")
            
            batch_number = 1
            batches = []
            # Process each channel
            for channel_id, channel_name in channels.items():
                print(f"\nProcessing channel: {channel_name}")
                # Stream messages in batches
                for batch in self.stream_channel_messages(extract_path, channel_name, users, batch_size):
                    if batch:
                        batches.append(batch)
            total_batches = len(batches)
            for idx, batch in enumerate(batches):
                is_final_batch = (idx == total_batches - 1)
                success = self.send_to_api(batch, idx + 1, is_final_batch)
                if not success:
                    print(f"Failed to send batch {idx + 1}")
                if delay > 0:
                    time.sleep(delay)
            print("\nExport processing completed!")
            
        finally:
            # Clean up temporary files
            
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)

def main():
    parser = argparse.ArgumentParser(description='Stream Slack export to API')
    parser.add_argument('zip_file', help='Path to Slack export zip file')
    parser.add_argument('api_url', help='API endpoint URL')
    parser.add_argument('--api-key', help='API authentication key')
    parser.add_argument('--batch-size', type=int, default=100, 
                       help='Number of messages per batch (default: 100)')
    parser.add_argument('--delay', type=float, default=0.1, 
                       help='Delay between API calls in seconds (default: 0.1)')
    parser.add_argument('--dry-run', action='store_true', help='Write payloads to a file instead of sending to API')
    parser.add_argument('--dry-run-file', default='dry_run_output.txt', help='File to write dry-run payloads (default: dry_run_output.txt)')
    
    args = parser.parse_args()
    
    # Validate zip file exists
    if not os.path.exists(args.zip_file):
        print(f"Error: Zip file '{args.zip_file}' not found")
        sys.exit(1)
    
    # Create streamer instance
    streamer = SlackExportStreamer(args.api_url, args.api_key, dry_run=args.dry_run, dry_run_file=args.dry_run_file)
    
    # Process the export
    try:
        streamer.process_export(
            args.zip_file, 
            batch_size=args.batch_size,
            delay=args.delay
        )
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()