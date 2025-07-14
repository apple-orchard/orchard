#!/bin/bash

# RAG System Startup Script (Production)
echo "🚀 Starting RAG System in production mode..."
echo "============================================="

# Check if dev.sh exists
if [ ! -f "dev.sh" ]; then
    echo "❌ dev.sh not found. Please ensure dev.sh is in the same directory."
    exit 1
fi

# Make sure dev.sh is executable
chmod +x dev.sh

# Call dev.sh with production mode
exec ./dev.sh prod 