"""Configuration schema for Google Drive plugin."""

# JSON Schema for Google Drive plugin configuration
GOOGLE_DRIVE_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["enabled", "auth_type", "config"],
    "properties": {
        "enabled": {
            "type": "boolean",
            "description": "Whether the Google Drive plugin is enabled"
        },
        "auth_type": {
            "type": "string",
            "enum": ["oauth", "service_account"],
            "description": "Authentication type to use"
        },
        "config": {
            "type": "object",
            "properties": {
                "oauth_config": {
                    "type": "object",
                    "properties": {
                        "client_id": {
                            "type": "string",
                            "description": "Google OAuth client ID"
                        },
                        "client_secret": {
                            "type": "string",
                            "description": "Google OAuth client secret"
                        },
                        "refresh_token": {
                            "type": "string",
                            "description": "Google OAuth refresh token"
                        }
                    },
                    "required": ["client_id", "client_secret", "refresh_token"]
                },
                "service_account_config": {
                    "type": "object",
                    "properties": {
                        "key_file": {
                            "type": "string",
                            "description": "Path to service account key file"
                        },
                        "delegated_user": {
                            "type": "string",
                            "format": "email",
                            "description": "Email of user to impersonate (optional)"
                        }
                    },
                    "required": ["key_file"]
                },
                "sources": {
                    "type": "array",
                    "description": "List of Google Drive sources to ingest",
                    "items": {
                        "type": "object",
                        "required": ["id"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Unique identifier for this source"
                            },
                            "drive_id": {
                                "type": "string",
                                "default": "root",
                                "description": "Drive ID or 'root' for My Drive"
                            },
                            "folder_id": {
                                "type": ["string", "null"],
                                "description": "Specific folder ID to ingest from"
                            },
                            "file_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "default": ["document", "spreadsheet", "presentation", "pdf"],
                                "description": "Types of files to include"
                            },
                            "exclude_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File name patterns to exclude (glob patterns)"
                            },
                            "include_shared": {
                                "type": "boolean",
                                "default": true,
                                "description": "Include files shared with the user"
                            },
                            "include_trashed": {
                                "type": "boolean",
                                "default": false,
                                "description": "Include trashed files"
                            },
                            "sync_mode": {
                                "type": "string",
                                "enum": ["full", "incremental"],
                                "default": "full",
                                "description": "Sync mode"
                            }
                        }
                    }
                }
            }
        }
    }
}


def validate_google_drive_config(config: dict) -> tuple[bool, list[str]]:
    """Validate Google Drive plugin configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    import jsonschema
    
    errors = []
    
    try:
        jsonschema.validate(instance=config, schema=GOOGLE_DRIVE_CONFIG_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
        return False, errors
    
    # Additional custom validation
    auth_type = config.get("auth_type", "oauth")
    google_config = config.get("config", {})
    
    # Validate auth configuration based on type
    if auth_type == "oauth":
        oauth_config = google_config.get("oauth_config", {})
        if not oauth_config:
            errors.append("OAuth configuration is required when auth_type is 'oauth'")
    elif auth_type == "service_account":
        sa_config = google_config.get("service_account_config", {})
        if not sa_config:
            errors.append("Service account configuration is required when auth_type is 'service_account'")
        else:
            import os
            key_file = sa_config.get("key_file", "")
            if key_file and not os.path.exists(os.path.expandvars(key_file)):
                errors.append(f"Service account key file not found: {key_file}")
    
    # Check for duplicate source IDs
    sources = google_config.get("sources", [])
    source_ids = [source.get("id") for source in sources]
    if len(source_ids) != len(set(source_ids)):
        errors.append("Duplicate source IDs found")
    
    return len(errors) == 0, errors 