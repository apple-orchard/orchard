#!/bin/bash

if [ "$DEBUG_MODE" = "true" ]; then
    echo "Starting server with debug mode (waiting for debugger to attach on port 5678)..."
    exec uv run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn main:app --host 0.0.0.0 --port 8011 --reload
else
    echo "Starting server in production mode..."
    exec uv run python main.py
fi
