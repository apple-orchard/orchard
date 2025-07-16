# Google Drive Ingestion Plugin

This plugin enables ingestion of documents from Google Drive into the RAG system, supporting Google Docs, Sheets, Presentations, and various other file formats.

## Features

- **Multiple Authentication Methods**: OAuth 2.0 and Service Account support
- **Flexible File Selection**: Ingest entire drives, specific folders, or filtered file types
- **Recursive Folder Traversal**: Optionally crawl all subfolders within a folder
- **Google Native Format Support**: Automatic conversion of Google Docs, Sheets, and Presentations
- **Standard File Support**: PDFs, Office documents, text files, and more
- **Incremental Sync**: Only process changed files on subsequent syncs
- **Pattern Filtering**: Include/exclude files based on name patterns
- **Shared Drive Support**: Access both personal and shared drives
- **Metadata Enrichment**: Preserve file metadata like owners, sharing status, and folder paths

## Configuration

Add the following to your `rag_config.yaml`:

### OAuth Authentication
```yaml
google_drive:
  enabled: true
  auth_type: "oauth"
  config:
    oauth_config:
      client_id: "${GOOGLE_CLIENT_ID}"
      client_secret: "${GOOGLE_CLIENT_SECRET}"
      refresh_token: "${GOOGLE_REFRESH_TOKEN}"
    sources:
      - id: "my-drive"
        drive_id: "root"  # "root" for My Drive
        folder_id: null   # null for entire drive, or specific folder ID
        file_types:
          - "document"    # Google Docs
          - "spreadsheet" # Google Sheets
          - "presentation" # Google Slides
          - "pdf"
        exclude_patterns:
          - "*.tmp"
          - "~$*"
          - "*.bak"
        include_shared: true
        include_trashed: false
        recursive: true  # Set to false to only scan the folder itself, not subfolders
        sync_mode: "incremental"
```

### Service Account Authentication
```yaml
google_drive:
  enabled: true
  auth_type: "service_account"
  config:
    service_account_config:
      key_file: "${GOOGLE_SERVICE_ACCOUNT_FILE}"
      delegated_user: "admin@company.com"  # Optional: for domain-wide delegation
    sources:
      - id: "shared-drive"
        drive_id: "0APHh4Ib7c3dUk9PVA"  # Shared drive ID
        folder_id: null
        file_types:
          - "document"
          - "spreadsheet"
          - "pdf"
        sync_mode: "full"
```

## Required Environment Variables

### For OAuth Authentication
```bash
# Google OAuth Credentials
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REFRESH_TOKEN=your_refresh_token_here
```

### For Service Account Authentication
```bash
# Path to service account JSON key file
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account-key.json
```

## Setting Up Authentication

### OAuth 2.0 Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing
   - Enable the Google Drive API

2. **Create OAuth Credentials**
   - Navigate to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials JSON

3. **Generate Refresh Token**
   - Use the [OAuth Playground](https://developers.google.com/oauthplayground/)
   - Authorize the Drive API scope: `https://www.googleapis.com/auth/drive.readonly`
   - Exchange authorization code for refresh token

### Service Account Setup (probably easiest)

1. **Create Service Account**
   - In Google Cloud Console, go to IAM & Admin > Service Accounts
   - Create a new service account
   - Download the JSON key file

2. **Enable Domain-Wide Delegation** (for G Suite/Workspace)
   - Edit the service account
   - Check "Enable G Suite Domain-wide Delegation"
   - Note the client ID

3. **Authorize in Admin Console** (for G Suite/Workspace)
   - Go to Google Admin Console
   - Security > API Controls > Domain-wide delegation
   - Add the service account client ID with Drive scopes

## Supported File Types

### Google Native Formats
- Google Docs (`application/vnd.google-apps.document`)
- Google Sheets (`application/vnd.google-apps.spreadsheet`)
- Google Slides (`application/vnd.google-apps.presentation`)
- Google Drawings (`application/vnd.google-apps.drawing`)
- Google Forms (`application/vnd.google-apps.form`)

### Standard Formats
- PDF (`application/pdf`)
- Microsoft Word (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
- Microsoft Excel (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)
- Microsoft PowerPoint (`application/vnd.openxmlformats-officedocument.presentationml.presentation`)
- Plain Text (`text/plain`)
- CSV (`text/csv`)
- Markdown (`text/markdown`)

## Usage

### API Endpoints

- `POST /api/plugins/google_drive/ingest` - Trigger ingestion
- `GET /api/plugins/google_drive/sources` - List configured sources
- `GET /api/plugins/google_drive/status/{job_id}` - Check ingestion status

### Example API Calls

```bash
# Trigger full sync
curl -X POST http://localhost:8011/api/plugins/google_drive/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "my-drive",
    "full_sync": true
  }'

# Trigger incremental sync
curl -X POST http://localhost:8011/api/plugins/google_drive/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "my-drive",
    "full_sync": false
  }'

# Check job status
curl http://localhost:8011/api/plugins/google_drive/status/{job_id}
```

## Best Practices

1. **Start with Specific Folders**: Test with a small folder before ingesting entire drives
2. **Use Exclude Patterns**: Filter out temporary and backup files
3. **Regular Incremental Syncs**: Schedule periodic incremental syncs to stay updated
4. **Monitor API Quotas**: Google Drive API has rate limits (default 1,000 requests per 100 seconds)
5. **Service Account for Production**: Use service accounts for automated/production environments

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify credentials are correctly set in environment variables
   - Check if tokens have expired (OAuth)
   - Ensure service account has necessary permissions

2. **No Files Found**
   - Check folder_id is correct
   - Verify file_types configuration includes desired formats
   - Ensure files aren't in trash (if include_trashed is false)
   - Check exclude_patterns aren't filtering out desired files

3. **Rate Limit Errors**
   - Google Drive API has quotas
   - Implement backoff/retry logic
   - Consider batching operations

4. **Permission Denied**
   - OAuth: User must have read access to files
   - Service Account: Needs to be shared with folders/files or have domain-wide delegation

### Debug Mode

Enable verbose logging in the reader:
```python
reader = GoogleDriveReaderWrapper(auth_config, auth_type, verbose=True)
```

## Metadata

Each ingested document includes the following metadata:
- `source_type`: "google_drive"
- `source_id`: Configured source ID
- `file_name`: Original file name
- `file_path`: Path in Google Drive
- `mime_type`: File MIME type
- `created_time`: File creation timestamp
- `modified_time`: Last modified timestamp
- `owners`: List of file owners
- `shared`: Whether file is shared
- `web_view_link`: Link to view in Google Drive

## Development

To extend this plugin:

1. Add new file type support in `reader.py`
2. Implement additional metadata extraction
3. Add new authentication methods
4. Enhance incremental sync with better change tracking

## License

This plugin is part of the Orchard RAG system and follows the same license terms. 