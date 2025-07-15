# GitHub Ingestion Plugin

This plugin enables ingestion of code and documentation from GitHub repositories into the RAG system.

## Features

- **Full Repository Sync**: Ingest entire repositories or specific paths
- **Incremental Updates**: Only process changed files on subsequent syncs
- **Path Filtering**: Include specific directories or files
- **Pattern Exclusion**: Exclude files matching specific patterns (e.g., `*.test.js`, `node_modules/`)
- **Branch Selection**: Choose which branch to ingest from
- **Metadata Enrichment**: Automatically adds GitHub-specific metadata to chunks

## Configuration

Add the following to your `rag_config.jsonc`:

```jsonc
{
  "plugins": {
    "github": {
      "enabled": true,
      "config": {
        "repositories": [
          {
            "id": "my-repo-1",
            "owner": "myorg",
            "repo": "myrepo",
            "branch": "main",
            "paths": ["src/", "docs/"],  // Optional: specific paths
            "exclude_patterns": ["*.test.js", "*.spec.ts", "node_modules/"],
            "sync_mode": "incremental"
          }
        ],
        "github_token": "${GITHUB_TOKEN}"  // Set GITHUB_TOKEN env variable
      }
    }
  }
}
```

## Required Environment Variables

- `GITHUB_TOKEN`: GitHub Personal Access Token with repository read permissions

### Creating a GitHub Token

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Click "Generate new token"
3. Give it a descriptive name
4. Select scopes:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories only)
5. Generate and copy the token
6. Set it as an environment variable: `export GITHUB_TOKEN=your_token_here`

## Usage

### API Endpoints

- `POST /api/plugins/github/ingest` - Trigger repository ingestion
- `GET /api/plugins/github/sources` - List configured repositories
- `GET /api/plugins/github/status/{job_id}` - Check ingestion job status

### Example API Calls

```bash
# Trigger full sync of a repository
curl -X POST http://localhost:8011/api/plugins/github/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "my-repo-1",
    "full_sync": true
  }'

# Trigger incremental sync
curl -X POST http://localhost:8011/api/plugins/github/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "my-repo-1",
    "full_sync": false
  }'

# Check job status
curl http://localhost:8011/api/plugins/github/status/{job_id}
```

## Metadata

The plugin adds the following metadata to each chunk:

- `source_type`: "github"
- `repository_owner`: Repository owner
- `repository_name`: Repository name
- `repository_full_name`: Full repository name (owner/repo)
- `branch`: Branch name
- `file_path`: Path to the file within the repository
- `file_type`: File extension
- `ingestion_timestamp`: When the file was ingested

## Best Practices

1. **Use Incremental Sync**: After the initial full sync, use incremental sync to save time
2. **Exclude Test Files**: Add patterns like `*.test.js`, `*.spec.ts` to exclude_patterns
3. **Focus on Relevant Paths**: Use the `paths` option to limit ingestion to relevant directories
4. **Regular Syncs**: Set up a schedule to sync repositories regularly
5. **Monitor Token Usage**: GitHub API has rate limits; monitor your usage

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Ensure GITHUB_TOKEN is set correctly
   - Verify token has necessary permissions
   - Check token hasn't expired

2. **Repository Not Found**
   - Verify owner and repo names are correct
   - Ensure token has access to private repositories

3. **Rate Limit Exceeded**
   - GitHub API has rate limits (5000 requests/hour for authenticated requests)
   - Use incremental sync to reduce API calls
   - Consider implementing request throttling

### Debug Mode

Enable verbose logging by setting:
```python
GithubRepositoryReader(verbose=True)
```

## Development

To extend this plugin:

1. Modify `reader.py` to add new filtering capabilities
2. Update `models.py` to add new configuration options
3. Enhance `plugin.py` to add new ingestion strategies

## License

This plugin is part of the Orchard RAG system and follows the same license terms. 