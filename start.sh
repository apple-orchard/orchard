#!/bin/bash

# RAG System Startup Script
echo "🚀 Starting RAG System..."
echo "=========================="

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running. Please start Ollama first:"
    echo "   ollama serve"
    echo ""
    echo "   Then pull the required model:"
    echo "   ollama pull llama3.1:8b"
    echo ""
    echo "   Or run the setup script:"
    echo "   python setup_ollama.py"
    exit 1
fi

echo "✅ Ollama is running"

# Check if Docker is available
if ! command -v docker > /dev/null 2>&1; then
    echo "⚠️  Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Docker is available"

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "⚠️  Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker Compose is available"

# Set up environment if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp env.example .env
fi

echo "🐳 Starting Docker containers..."
docker-compose up -d

echo ""
echo "🎉 RAG System is starting up!"
echo ""
echo "📱 Frontend will be available at: http://localhost:3000"
echo "🔧 Backend API will be available at: http://localhost:8011"
echo "📚 API Documentation: http://localhost:8011/docs"
echo ""
echo "⏳ Please wait a moment for the containers to fully start..."
echo "📋 You can check the logs with: docker-compose logs -f"
echo "🛑 To stop the system: docker-compose down" 