# Slack Export Streamer CLI

A command-line tool to process Slack export zip files and stream their contents to a specified API endpoint in batches with automatic resume capability.

## Features
- Extracts and processes Slack export zip files
- Enriches messages with channel and user info
- Streams messages in configurable batches to an API
- **Resume functionality** - automatically saves progress and can resume from where it left off
- Supports API authentication via key
- Handles errors and reports progress with batch numbers
- Dry-run mode for testing without sending data

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
python slack_streamer.py <zip_file> <api_url> [options]
```

### Arguments
- `<zip_file>`: Path to the Slack export zip file
- `<api_url>`: Base URL of the API to stream data to

### Options
- `--api-key`: API authentication key (optional)
- `--batch-size`: Number of messages per batch (default: 100)
- `--delay`: Delay in seconds between API calls (default: 0.1)
- `--dry-run`: Write payloads to a file instead of sending to the API (for testing/debugging)
- `--dry-run-file`: File to write dry-run payloads (default: dry_run_output.txt)
- `--resume`: Resume from last saved progress (use after interruption)

### Examples

#### Basic Usage
```sh
python slack_streamer.py export.zip https://your.api/endpoint --api-key YOUR_KEY --batch-size 200 --delay 0.2
```

#### Dry Run (Testing)
To test what would be sent to the API without actually making requests:
```sh
python slack_streamer.py export.zip https://your.api/endpoint --dry-run
```
This will write each batch payload to `dry_run_output.txt` (or a file you specify with `--dry-run-file`).

#### Resume After Interruption
If the process is interrupted (Ctrl+C, network error, etc.), you can resume from where it left off:
```sh
python slack_streamer.py export.zip https://your.api/endpoint --resume
```

## Resume Functionality

The tool automatically saves progress to `slack_export_progress.json` after each batch is processed. This allows you to:

- **Interrupt safely** - Press Ctrl+C or handle network errors without losing progress
- **Resume exactly** - Continue from the exact batch where processing stopped
- **Skip completed work** - Already processed channels are automatically skipped

### Progress File Format
```json
{
  "current_batch": 15,
  "total_batches": 45,
  "current_channel": "general",
  "processed_channels": ["announcements", "random"],
  "current_channel_batch": 3,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Resume Workflow
1. **Start processing**: `python slack_streamer.py export.zip https://api.example.com`
2. **Interruption occurs**: Process stops (Ctrl+C, network error, etc.)
3. **Progress saved**: `slack_export_progress.json` contains current state
4. **Resume**: `python slack_streamer.py export.zip https://api.example.com --resume`
5. **Continues**: Skips completed channels and continues from exact batch

## How It Works
1. Extracts the Slack export zip to a temporary directory
2. Loads channel and user metadata
3. **Counts total batches** for progress tracking
4. Iterates through each channel and its message files, enriching messages
5. **Sends messages in batches** to the API with batch numbers
6. **Saves progress** after each batch for resume capability
7. Cleans up temporary files after processing

## Progress and Logging

The tool provides detailed progress information:
- **Batch numbering**: Each batch is numbered sequentially (e.g., "Successfully sent batch 15 of 45 messages to API")
- **Channel progress**: Shows which channel is currently being processed
- **Resume information**: When resuming, shows exactly where it's continuing from
- **Error handling**: Failed batches are logged with batch numbers for easy identification

## API Expectations
- The script sends POST requests to the API URL with a JSON body in the following format:

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

- Only messages with a non-empty `content.text` field are included in `documents`
- `batch_number` in metadata corresponds to the sequential batch number being processed
- `is_final_batch` indicates when the last batch is being sent

## Error Handling

- **Network errors**: Progress is saved before each API call, so you can resume after network issues
- **API errors**: Failed batches are logged with batch numbers for debugging
- **File errors**: JSON parsing errors are logged but don't stop processing
- **Interruption**: Ctrl+C safely saves progress and exits

## Files Created

- `slack_export_progress.json`: Progress tracking file (auto-created, auto-deleted on completion)
- `dry_run_output.txt`: Dry-run output file (if using --dry-run)
- Temporary extraction directory: Auto-created and cleaned up

## License
MIT 