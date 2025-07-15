"""Configuration schema for GitHub plugin."""

# JSON Schema for GitHub plugin configuration
GITHUB_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["enabled", "config"],
    "properties": {
        "enabled": {
            "type": "boolean",
            "description": "Whether the GitHub plugin is enabled"
        },
        "config": {
            "type": "object",
            "required": ["repositories"],
            "properties": {
                "repositories": {
                    "type": "array",
                    "description": "List of GitHub repositories to ingest",
                    "items": {
                        "type": "object",
                        "required": ["id", "owner", "repo"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Unique identifier for this repository configuration"
                            },
                            "owner": {
                                "type": "string",
                                "description": "Repository owner (user or organization)"
                            },
                            "repo": {
                                "type": "string",
                                "description": "Repository name"
                            },
                            "branch": {
                                "type": "string",
                                "default": "main",
                                "description": "Branch to ingest from"
                            },
                            "paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific paths to include (optional)"
                            },
                            "exclude_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File patterns to exclude (glob patterns)"
                            },
                            "last_synced": {
                                "type": ["string", "null"],
                                "format": "date-time",
                                "description": "Last sync timestamp"
                            },
                            "sync_mode": {
                                "type": "string",
                                "enum": ["full", "incremental"],
                                "default": "full",
                                "description": "Sync mode"
                            }
                        }
                    }
                },
                "github_token": {
                    "type": "string",
                    "description": "GitHub personal access token (can use ${GITHUB_TOKEN} for env var)"
                }
            }
        }
    }
}


def validate_github_config(config: dict) -> tuple[bool, list[str]]:
    """Validate GitHub plugin configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    import jsonschema
    
    errors = []
    
    try:
        jsonschema.validate(instance=config, schema=GITHUB_CONFIG_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
        return False, errors
    
    # Additional custom validation
    github_config = config.get("config", {})
    
    # Check for duplicate repository IDs
    repositories = github_config.get("repositories", [])
    repo_ids = [repo.get("id") for repo in repositories]
    if len(repo_ids) != len(set(repo_ids)):
        errors.append("Duplicate repository IDs found")
    
    # Validate repository names
    for repo in repositories:
        owner = repo.get("owner", "")
        repo_name = repo.get("repo", "")
        
        if not owner or not repo_name:
            errors.append(f"Invalid repository: {owner}/{repo_name}")
        
        # Check for valid GitHub username/repo format
        import re
        if not re.match(r'^[\w.-]+$', owner):
            errors.append(f"Invalid owner name: {owner}")
        if not re.match(r'^[\w.-]+$', repo_name):
            errors.append(f"Invalid repository name: {repo_name}")
    
    return len(errors) == 0, errors 