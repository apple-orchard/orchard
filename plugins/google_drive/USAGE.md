# Google Drive Plugin Usage Guide

This guide provides step-by-step instructions for using the Google Drive plugin with Orchard RAG.

## Quick Start

### 1. Set Up OAuth Authentication (Easiest Method)

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Create Project" and give it a name
3. Wait for project creation to complete

#### Step 2: Enable Google Drive API
1. In your project, go to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"

#### Step 3: Create OAuth Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "+ CREATE CREDENTIALS" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - Choose "External" user type
   - Fill in required fields (app name, user support email)
   - Add your email to test users
   - Save and continue
4. Back in credentials, create OAuth client ID:
   - Application type: "Desktop app"
   - Name: "Orchard RAG"
   - Click "Create"
5. Download the credentials JSON file

#### Step 4: Get Refresh Token
1. Visit [Google OAuth Playground](https://developers.google.com/oauthplayground/)
2. Click the gear icon (settings) and check "Use your own OAuth credentials"
3. Enter your Client ID and Client Secret from the downloaded JSON
4. In Step 1, select "Google Drive API v3" and check:
   - `https://www.googleapis.com/auth/drive.readonly`
5. Click "Authorize APIs" and sign in with your Google account
6. Click "Exchange authorization code for tokens"
7. Copy the "Refresh token" value

### 2. Configure Environment

Add to your `.env` file:
```bash
# Google Drive OAuth
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REFRESH_TOKEN=your_refresh_token_here
```

### 3. Update Configuration

Add to `rag_config.yaml`:
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
      - id: "my-documents"
        drive_id: "root"
        folder_id: null  # Or specific folder ID
        file_types:
          - "document"
          - "spreadsheet"
          - "pdf"
        exclude_patterns:
          - "*.tmp"
          - "~*"
        sync_mode: "incremental"
```

### 4. Start Ingestion

Using the CLI:
```bash
# List available sources
./orchard plugins list

# Start ingestion
./orchard plugins ingest google_drive --source-id my-documents

# Check status
./orchard plugins status google_drive <job_id>
```

Using the API:
```bash
# Trigger ingestion
curl -X POST http://localhost:8011/api/plugins/google_drive/ingest \
  -H "Content-Type: application/json" \
  -d '{"source_id": "my-documents"}'
```

## Common Use Cases

### Ingest a Specific Folder

To get a folder ID:
1. Open the folder in Google Drive
2. Look at the URL: `https://drive.google.com/drive/folders/FOLDER_ID`
3. Copy the FOLDER_ID part

Configuration:
```yaml
sources:
  - id: "project-docs"
    drive_id: "root"
    folder_id: "1a2b3c4d5e6f7g8h9i0j"  # Your folder ID
    file_types: ["document", "spreadsheet", "pdf"]
    sync_mode: "incremental"
```

### Ingest Shared Drives

For Google Workspace users with shared drives:

1. Get the shared drive ID:
   - Open the shared drive
   - URL will be: `https://drive.google.com/drive/folders/DRIVE_ID`

2. Configure:
```yaml
sources:
  - id: "team-drive"
    drive_id: "0APHh4Ib7c3dUk9PVA"  # Shared drive ID
    folder_id: null
    file_types: ["document", "spreadsheet", "presentation", "pdf"]
    include_shared: true
    sync_mode: "incremental"
```

### Filter by File Types

Ingest only specific file types:
```yaml
sources:
  - id: "docs-only"
    drive_id: "root"
    file_types: ["document"]  # Only Google Docs
    
  - id: "data-files"
    drive_id: "root"
    file_types: ["spreadsheet", "csv"]  # Sheets and CSV files
    
  - id: "presentations"
    drive_id: "root"
    file_types: ["presentation", "pdf"]  # Slides and PDFs
```

### Exclude Patterns

Skip files matching certain patterns:
```yaml
sources:
  - id: "clean-docs"
    drive_id: "root"
    exclude_patterns:
      - "*.tmp"        # Temporary files
      - "~*"           # Backup files
      - "Draft*"       # Files starting with "Draft"
      - "*_old.*"      # Old versions
      - "*.bak"        # Backup files
      - "Copy of *"    # Duplicate files
```

## Service Account Setup (For Production)

### Step 1: Create Service Account
1. In Google Cloud Console, go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Name it (e.g., "orchard-rag-reader")
4. Grant role: "Viewer" (basic read access)
5. Create and download JSON key

### Step 2: Share Files/Folders
Share the Google Drive folders with the service account email:
1. Right-click folder in Google Drive
2. Click "Share"
3. Add the service account email (e.g., `orchard-rag@project.iam.gserviceaccount.com`)
4. Set permission to "Viewer"

### Step 3: Configure
```yaml
google_drive:
  enabled: true
  auth_type: "service_account"
  config:
    service_account_config:
      key_file: "${GOOGLE_SERVICE_ACCOUNT_FILE}"
    sources:
      - id: "shared-folders"
        drive_id: "root"
        file_types: ["document", "spreadsheet", "pdf"]
```

Environment variable:
```bash
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account-key.json
```

## Monitoring Ingestion

### Check Progress
```bash
# Using CLI
./orchard plugins status google_drive <job_id>

# Using API
curl http://localhost:8011/api/plugins/google_drive/status/<job_id>
```

Example response:
```json
{
  "job_id": "abc123",
  "status": "running",
  "progress": {
    "processed_documents": 45,
    "total_documents": 100,
    "percentage": 45
  },
  "metadata": {
    "current_action": "chunking",
    "details": "Creating chunks from 45 documents"
  }
}
```

### View Logs
Check Docker logs for detailed information:
```bash
docker-compose logs -f app | grep google_drive
```

## Incremental Sync

After initial ingestion, use incremental sync for updates:

```bash
# CLI - incremental sync
./orchard plugins ingest google_drive --source-id my-documents --incremental

# API - incremental sync
curl -X POST http://localhost:8011/api/plugins/google_drive/ingest \
  -H "Content-Type: application/json" \
  -d '{"source_id": "my-documents", "full_sync": false}'
```

Incremental sync will:
- Only process files changed since last sync
- Add new files
- Update modified files
- Skip unchanged files

## Troubleshooting

### "No files found"
- Check folder permissions
- Verify folder_id is correct
- Ensure file_types includes your files
- Check exclude_patterns aren't too broad

### "Authentication failed"
- Verify environment variables are set
- Check if refresh token is valid
- For service accounts, ensure JSON file path is correct

### "Rate limit exceeded"
- Google Drive API has quotas (1000 requests per 100 seconds)
- Wait a few minutes and retry
- Consider smaller batch sizes

### View ingested content
Check what was ingested:
```bash
# Using CLI
./orchard rag info

# Query specific content
./orchard rag query "show me content from Google Drive"
```

## Best Practices

1. **Test with small folders first**: Start with a folder containing a few files
2. **Use specific folder IDs**: More efficient than scanning entire drive
3. **Set up incremental sync**: Schedule regular updates (e.g., daily)
4. **Monitor first ingestion**: Watch logs to ensure files are processed correctly
5. **Use exclude patterns**: Filter out drafts, temps, and backups

## Example Configurations

### Personal Knowledge Base
```yaml
sources:
  - id: "personal-notes"
    drive_id: "root"
    folder_id: "1ABC..."  # Your notes folder
    file_types: ["document", "pdf"]
    exclude_patterns: ["Draft*", "*.tmp"]
    sync_mode: "incremental"
```

### Team Documentation
```yaml
sources:
  - id: "team-wiki"
    drive_id: "0XYZ..."  # Shared drive ID
    file_types: ["document", "spreadsheet", "presentation"]
    include_shared: true
    sync_mode: "incremental"
```

### Research Papers
```yaml
sources:
  - id: "research"
    drive_id: "root"
    folder_id: "1DEF..."  # Research folder
    file_types: ["pdf"]
    exclude_patterns: ["*.tmp", "*_annotated.pdf"]
    sync_mode: "full"  # Full sync to catch moves/renames
``` 