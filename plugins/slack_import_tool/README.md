# Slack Export Streamer CLI

A command-line tool to process Slack export zip files and stream their contents to a specified API endpoint in batches.

## Features
- Extracts and processes Slack export zip files
- Enriches messages with channel and user info
- Streams messages in configurable batches to an API
- Supports API authentication via key
- Handles errors and reports progress

## Requirements
- Python 3.7+
- [requests](https://pypi.org/project/requests/)

## Installation
1. Clone this repository or copy `slack_streamer.py` to your project directory.
2. Install dependencies:
   ```sh
   pip install requests
   ```

## Usage
```sh
python slack_streamer.py <zip_file> <api_url> [--api-key API_KEY] [--batch-size N] [--delay SECONDS]
```

### Arguments
- `<zip_file>`: Path to the Slack export zip file
- `<api_url>`: Base URL of the API to stream data to

### Options
- `--api-key`: API authentication key (optional)
- `--batch-size`: Number of messages per batch (default: 100)
- `--delay`: Delay in seconds between API calls (default: 0.1)
- `--endpoint`: API endpoint path (default: none; if set, appended to base URL)
- `--dry-run`: Write payloads to a file instead of sending to the API (for testing/debugging)
- `--dry-run-file`: File to write dry-run payloads (default: dry_run_output.txt)

### Example
```sh
python slack_streamer.py export.zip https://your.api/endpoint --api-key YOUR_KEY --batch-size 200 --delay 0.2
```

#### Dry Run Example
To test what would be sent to the API without actually making requests:
```sh
python slack_streamer.py export.zip https://your.api/endpoint --dry-run
```
This will write each batch payload to `dry_run_output.txt` (or a file you specify with `--dry-run-file`).

## How It Works
1. Extracts the Slack export zip to a temporary directory.
2. Loads channel and user metadata.
3. Iterates through each channel and its message files, enriching messages.
4. Sends messages in batches to the API as JSON payloads.
5. Cleans up temporary files after processing.

## API Expectations
- The script sends POST requests to the API URL (and optional endpoint) with a JSON body in the following format:

```json
{
  "batch_id": "string (uuid)",
  "documents": [
    {
      "document_id": "string (unique per message)",
      "document_type": "message|thread|file",
      "channel": {
        "id": "string",
        "name": "string",
        "is_private": "boolean"
      },
      "content": {
        "text": "string",
        "formatted_text": "string (optional, for rich formatting)",
        "attachments": [
          {
            "type": "file|image|link",
            "url": "string",
            "filename": "string",
            "title": "string"
          }
        ]
      },
      "metadata": {
        "timestamp": "ISO 8601 timestamp",
        "user_id": "string",
        "user_name": "string",
        "thread_ts": "string (optional, for threaded messages)",
        "parent_message_id": "string (optional)",
        "reactions": [
          {
            "emoji": "string",
            "count": "number",
            "users": ["string"]
          }
        ],
        "edited_timestamp": "ISO 8601 timestamp (optional)",
        "message_type": "regular|bot|system"
      }
    }
    // ... more documents ...
  ],
  "batch_metadata": {
    "batch_number": "number",
    "is_final_batch": "boolean"
  }
}
```

- Only messages with a non-empty `content.text` field are included in `documents`.
- `workspace_info` is omitted.
- Batching and batch metadata are handled automatically by the tool.

## License
MIT 