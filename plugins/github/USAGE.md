# GitHub Plugin Usage Guide

## Quick Start

### 1. Set up GitHub Token

Create a GitHub Personal Access Token:
```bash
export GITHUB_TOKEN=your_github_token_here
```

### 2. Configure a Repository

Edit `rag_config.yaml`:
```yaml
plugins:
  github:
    enabled: true
    config:
      repositories:
        - id: my-repo
          owner: myusername
          repo: myproject
          branch: main
          paths:
            - src/
          exclude_patterns:
            - "*.test.js"
            - node_modules/
          sync_mode: full
      github_token: ${GITHUB_TOKEN}
```

### 3. Start the Services

```bash
# Start the application
docker-compose up -d

# Or for development
./dev.sh
```

### 4. Trigger Repository Ingestion

```bash
# Full sync
curl -X POST http://localhost:8011/api/plugins/github/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "my-repo",
    "full_sync": true
  }'

# Response:
# {
#   "job_id": "123e4567-e89b-12d3-a456-426614174000",
#   "plugin_name": "github",
#   "source_id": "my-repo",
#   "sync_type": "full"
# }
```

### 5. Check Ingestion Status

```bash
curl http://localhost:8011/api/plugins/github/status/123e4567-e89b-12d3-a456-426614174000

# Response:
# {
#   "id": "123e4567-e89b-12d3-a456-426614174000",
#   "plugin_name": "github",
#   "status": "completed",
#   "started_at": "2024-01-01T12:00:00",
#   "completed_at": "2024-01-01T12:05:00",
#   "total_documents": 150,
#   "processed_documents": 150,
#   "failed_documents": 0
# }
```

### 6. Query the Ingested Content

```bash
curl -X POST http://localhost:8011/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does the authentication system work?",
    "max_chunks": 5
  }'
```

## Advanced Usage

### List All Configured Repositories

```bash
curl http://localhost:8011/api/plugins/github/sources
```

### Update Plugin Configuration via API

```bash
curl -X PUT http://localhost:8011/api/plugins/github/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "config": {
      "repositories": [...],
      "github_token": "${GITHUB_TOKEN}"
    }
  }'
```

### Incremental Sync

After the initial full sync, use incremental sync to update only changed files:

```bash
curl -X POST http://localhost:8011/api/plugins/github/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "my-repo",
    "full_sync": false
  }'
```

## Frontend Integration

The frontend will provide a UI for:
1. Configuring repositories
2. Triggering syncs
3. Monitoring ingestion progress
4. Viewing sync history

## Troubleshooting

### Check Plugin Status

```bash
curl http://localhost:8011/api/plugins
```

### View All Jobs

```bash
curl http://localhost:8011/api/plugins/github/jobs
```

### Enable Debug Logging

Set in your environment:
```bash
export LOG_LEVEL=DEBUG
```