# Async Ingestion System

This document describes the async ingestion system that allows document processing to run in the background without blocking the API.

## Overview

The async ingestion system consists of:

1. **Background Job Manager** (`app/services/ingestion_jobs.py`) - Manages job queue and execution
2. **Async API Endpoints** - Return job IDs immediately instead of waiting for completion
3. **Job Status Tracking** - Monitor progress and results
4. **Frontend Integration** - Optional UI components for job management

## Key Features

### ✅ Non-Blocking Processing
- Ingestion requests return immediately with job ID
- Large files and batch operations don't block the API
- Multiple jobs can run concurrently (default: 3 concurrent jobs)

### ✅ Progress Tracking
- Real-time job status updates
- Progress percentages for running jobs
- Detailed error messages for failed jobs

### ✅ Job Management
- List all jobs with filtering by status
- Cancel pending jobs
- Automatic cleanup of old completed jobs
- Job statistics and metrics

## API Endpoints

### Main Ingestion Endpoints (Async by Default)

#### POST `/ingest`
Document ingestion - **NOW ASYNC BY DEFAULT**
```bash
# Async mode (default)
curl -X POST "http://localhost:8011/ingest" \
  -F "text_content=Your document text here" \
  -F "metadata={\"source\":\"api\"}"

# Sync mode (backwards compatibility)
curl -X POST "http://localhost:8011/ingest" \
  -F "text_content=Your document text here" \
  -F "metadata={\"source\":\"api\"}" \
  -F "sync=true"
```

#### POST `/ingest/batch`
Batch message ingestion - **NOW ASYNC BY DEFAULT**
```bash
# Async mode (default)
curl -X POST "http://localhost:8011/ingest/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"text": "Message 1", "metadata": {"id": "1"}},
      {"text": "Message 2", "metadata": {"id": "2"}}
    ],
    "metadata": {"batch_source": "slack"}
  }'

# Sync mode (backwards compatibility)
curl -X POST "http://localhost:8011/ingest/batch?sync=true" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"text": "Message 1", "metadata": {"id": "1"}},
      {"text": "Message 2", "metadata": {"id": "2"}}
    ],
    "metadata": {"batch_source": "slack"}
  }'
```

Returns (async mode):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "text_ingestion",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "message": ""
}
```

### Alternative Async Endpoints (Explicit)

#### POST `/ingest/async`
Explicit async document ingestion (same as `/ingest` without sync=true)

#### POST `/ingest/text/async`
Explicit async text ingestion
```bash
curl -X POST "http://localhost:8011/ingest/text/async" \
  -H "Content-Type: application/json" \
  -d '{"text_content": "Document text", "metadata": {"source": "api"}}'
```

#### POST `/ingest/batch/async`
Explicit async batch ingestion (same as `/ingest/batch` without sync=true)

### Job Management Endpoints

#### GET `/jobs/{job_id}`
Get detailed status of a specific job
```bash
curl "http://localhost:8011/jobs/550e8400-e29b-41d4-a716-446655440000"
```

Returns:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "text_ingestion",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:01Z",
  "completed_at": "2024-01-15T10:30:05Z",
  "progress": 1.0,
  "message": "Text ingested successfully",
  "error_message": "",
  "chunks_created": 5,
  "total_items": 1,
  "processed_items": 1,
  "metadata": {...}
}
```

#### GET `/jobs`
List all jobs with optional status filtering
```bash
# All jobs
curl "http://localhost:8011/jobs"

# Only running jobs
curl "http://localhost:8011/jobs?status=running"

# Limit results
curl "http://localhost:8011/jobs?limit=10"
```

#### DELETE `/jobs/{job_id}`
Cancel a pending job
```bash
curl -X DELETE "http://localhost:8011/jobs/550e8400-e29b-41d4-a716-446655440000"
```

#### GET `/jobs/stats`
Get job statistics
```bash
curl "http://localhost:8011/jobs/stats"
```

Returns:
```json
{
  "total_jobs": 25,
  "pending": 2,
  "running": 1,
  "completed": 20,
  "failed": 2,
  "cancelled": 0,
  "total_chunks_created": 1250
}
```

## Job Statuses

- **pending** - Job created but not started yet
- **running** - Job is currently being processed
- **completed** - Job finished successfully
- **failed** - Job encountered an error
- **cancelled** - Job was cancelled by user

## Testing

Use the provided test script to verify functionality:

```bash
# Install requests if needed
pip install requests

# Run tests
python test_async_ingestion.py
```

The test script will:
1. Test async text ingestion
2. Test async batch ingestion
3. Monitor job progress to completion
4. Test job listing and statistics
5. Verify querying works after ingestion

## Implementation Details

### Job Manager Configuration

The job manager can be configured with:
- `max_concurrent_jobs` - Maximum jobs running simultaneously (default: 3)
- `max_age_hours` - How long to keep old jobs (default: 24 hours)
- `max_jobs` - Maximum total jobs to keep (default: 100)

### Automatic Cleanup

- Old completed/failed jobs are cleaned up automatically every hour
- Active jobs (pending/running) are never cleaned up
- Cleanup keeps most recent jobs within limits

### Error Handling

- Jobs that fail include detailed error messages
- Temporary files are cleaned up automatically
- Failed jobs don't affect other jobs in the queue

## Integration with Existing Code

**IMPORTANT UPDATE**: The main ingestion endpoints now use async mode by default!

### Current Endpoint Behavior:

- **Async by Default**: `/ingest`, `/ingest/batch` - Return job ID immediately
- **Sync Option Available**: Add `sync=true` parameter to use blocking mode
- **Always Synchronous**: `/ingest/text`, `/ingest/file` - Still block until complete
- **Always Asynchronous**: `/ingest/async`, `/ingest/text/async`, `/ingest/batch/async` - Return immediately

### Backwards Compatibility:

To maintain backwards compatibility with existing code, add `sync=true`:

```bash
# Old behavior (now requires sync=true)
curl -X POST "http://localhost:8011/ingest" \
  -F "text_content=Document text" \
  -F "sync=true"

# New default behavior (async)
curl -X POST "http://localhost:8011/ingest" \
  -F "text_content=Document text"
```

Both systems use the same underlying ingestion logic, so results are identical.

## Frontend Integration

A `JobManager` component is provided (`frontend/src/components/JobManager.tsx`) that can be integrated into the UI to:

- Display running jobs with progress bars
- Show job statistics
- Allow cancelling pending jobs
- Auto-refresh job status
- Show job history

To integrate:
1. Import the component: `import JobManager from './components/JobManager';`
2. Add to your UI: `<JobManager />`
3. The component handles all API calls and state management

## Benefits

### For Users
- Upload large files without waiting
- Process multiple documents simultaneously
- Get immediate feedback that request was received
- Monitor progress of long-running operations

### For Developers
- API remains responsive during heavy processing
- Better resource utilization with concurrent processing
- Detailed job tracking for debugging
- Easy to extend with new job types

### For System Operations
- Prevents API timeouts on large operations
- Automatic job cleanup prevents memory leaks
- Job statistics for monitoring system usage
- Graceful handling of failures

## Migration from Sync to Async

To migrate existing integrations:

1. **Replace endpoint URLs**: Add `/async` suffix
2. **Handle job IDs**: Store job ID and poll for status
3. **Update client logic**: Check job completion before proceeding
4. **Add error handling**: Handle job failures appropriately

Example migration:
```python
# Before (synchronous)
response = requests.post("/ingest/text", json={"text_content": text})
if response.json()["success"]:
    print(f"Created {response.json()['chunks_created']} chunks")

# After (asynchronous)
response = requests.post("/ingest/text/async", json={"text_content": text})
job_id = response.json()["job_id"]

# Poll for completion
while True:
    status = requests.get(f"/jobs/{job_id}").json()
    if status["status"] == "completed":
        print(f"Created {status['chunks_created']} chunks")
        break
    elif status["status"] == "failed":
        print(f"Job failed: {status['error_message']}")
        break
    time.sleep(1)
```

## Configuration

No additional configuration is required. The async system starts automatically with the API server and uses sensible defaults.

Advanced configuration can be done by modifying the job manager initialization in `app/api/main.py`.