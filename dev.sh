#!/bin/bash

# Development helper script for Orchard RAG System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if Ollama is running
check_ollama() {
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_error "Ollama is not running. Please start Ollama first:"
        echo "   ollama serve"
        echo ""
        echo "   Then pull the required model:"
        echo "   ollama pull llama3.1:8b"
        echo ""
        echo "   Or run the setup script:"
        echo "   python setup_ollama.py"
        exit 1
    fi
    print_status "Ollama is running"
}

# Function to set up environment
setup_env() {
    if [ ! -f .env ]; then
        print_status "Creating .env file..."
        cp env.example .env
    fi
}

# Function to stop any conflicting processes
cleanup() {
    print_status "Cleaning up any existing processes..."
    
    # Kill any React dev servers
    pkill -f "node.*react-scripts" || true
    
    # Stop any existing Docker containers
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    print_status "Cleanup completed."
}

# Function to start development environment
start_dev() {
    local debug_mode="false"
    
    # Parse debug flag
    while [[ $# -gt 0 ]]; do
        case $1 in
            --debug)
                debug_mode="true"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    print_status "Starting development environment..."
    
    if [ "$debug_mode" = "true" ]; then
        print_status "Debug mode enabled - server will wait for debugger to attach on port 5678"
    fi
    
    check_docker
    check_ollama
    setup_env
    cleanup
    
    # Set debug mode environment variable
    export DEBUG_MODE="$debug_mode"
    
    # Build and start development containers
    print_status "Building and starting containers..."
    docker-compose -f docker-compose.dev.yml up --build -d
    
    print_status "Development environment started!"
    print_status "Frontend: http://localhost:3000"
    print_status "Backend API: http://localhost:8011"
    print_status "API Documentation: http://localhost:8011/docs"
    
    if [ "$debug_mode" = "true" ]; then
        print_status "🐛 Debug mode is enabled!"
        print_status "   - Server is waiting for debugger to attach on port 5678"
        print_status "   - Use VSCode 'Python Debugger: Attach to Docker' configuration"
        print_status "   - Or connect any debugger to localhost:5678"
    fi
    
    print_status "Showing logs... (Press Ctrl+C to stop viewing logs)"
    docker-compose -f docker-compose.dev.yml logs -f
}

# Function to start production environment
start_prod() {
    print_status "Starting production environment..."
    
    check_docker
    check_ollama
    setup_env
    cleanup
    
    # Build and start production containers
    print_status "Building and starting containers..."
    docker-compose up --build -d
    
    print_status "Production environment started!"
    print_status "Frontend: http://localhost:3000"
    print_status "Backend API: http://localhost:8011"
    print_status "API Documentation: http://localhost:8011/docs"
    print_status ""
    print_status "⏳ Please wait a moment for containers to fully start..."
    print_status "📋 Check logs with: docker-compose logs -f"
    print_status "🛑 Stop with: docker-compose down"
}

# Function to stop environment
stop() {
    print_status "Stopping environment..."
    
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    print_status "Environment stopped."
}

# Function to show logs
logs() {
    if [ -f "docker-compose.dev.yml" ] && docker-compose -f docker-compose.dev.yml ps -q > /dev/null 2>&1; then
        docker-compose -f docker-compose.dev.yml logs -f
    else
        docker-compose logs -f
    fi
}

# Function to rebuild containers
rebuild() {
    print_status "Rebuilding containers..."
    
    stop
    
    # Remove existing images
    docker-compose -f docker-compose.dev.yml down --rmi all 2>/dev/null || true
    docker-compose down --rmi all 2>/dev/null || true
    
    start_dev "$@"
}

# Function to show help
show_help() {
    echo "Orchard RAG System Development Helper"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  dev     Start development environment with hot reloading"
    echo "  prod    Start production environment"
    echo "  stop    Stop all environments"
    echo "  logs    Show logs from running containers"
    echo "  rebuild Rebuild and restart development environment"
    echo "  cleanup Clean up processes and containers"
    echo "  help    Show this help message"
    echo ""
    echo "Options for 'dev' and 'rebuild' commands:"
    echo "  --debug Enable debug mode (server waits for debugger to attach on port 5678)"
    echo ""
    echo "Examples:"
    echo "  $0 dev               # Start development environment"
    echo "  $0 dev --debug       # Start development environment with debugging enabled"
    echo "  $0 rebuild           # Rebuild and restart development"
    echo "  $0 rebuild --debug   # Rebuild and restart development with debugging enabled"
    echo "  $0 stop              # Stop all containers"
    echo ""
    echo "Prerequisites:"
    echo "  • Docker and Docker Compose installed"
    echo "  • Ollama running (ollama serve)"
    echo "  • Required model pulled (ollama pull llama3.1:8b)"
}

# Main script logic
case "${1:-help}" in
    dev|development)
        shift
        start_dev "$@"
        ;;
    prod|production)
        start_prod
        ;;
    stop)
        stop
        ;;
    logs)
        logs
        ;;
    rebuild)
        shift
        rebuild "$@"
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 