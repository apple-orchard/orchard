#!/bin/bash

# Function to check if models exist and download if needed
ensure_models() {
    echo "🔍 Checking for cached models..."
    
    # Create data directories if they don't exist
    mkdir -p /app/data/model_cache
    mkdir -p /app/data/chroma_db
    
    # Check if model cache directory has models
    if [ -d "/app/data/model_cache" ] && [ "$(ls -A /app/data/model_cache 2>/dev/null | grep -E '^models--' | wc -l)" -gt 0 ]; then
        echo "✅ Embedding models already cached"
    else
        echo "📥 Embedding models not found, downloading..."
        
        # Download models using the existing script
        cd /app
        uv run python download_models.py
        
        echo "✅ Embedding model download complete"
    fi
}

# Ensure embedding models are available before starting the server
ensure_models

if [ "$DEBUG_MODE" = "true" ]; then
    echo "Starting server with debug mode (waiting for debugger to attach on port 5678)..."
    exec uv run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn main:app --host 0.0.0.0 --port 8011 --reload
else
    echo "Starting server in production mode..."
    exec uv run python -m uvicorn main:app --host 0.0.0.0 --port 8011 --reload
fi
