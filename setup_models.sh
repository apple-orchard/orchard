#!/bin/bash
"""
Model Setup Script
Downloads and caches models locally before running Docker containers.
"""

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}🔧 MODEL CACHE SETUP${NC}"
    echo "=============================="
}

print_section() {
    echo -e "\n${YELLOW}$1${NC}"
    echo "----------------------------"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check requirements
check_requirements() {
    print_section "Checking Requirements"

    # Check Python/uv
    if command -v uv >/dev/null 2>&1; then
        print_success "uv found"
    else
        print_error "uv not found - install from https://docs.astral.sh/uv/"
        exit 1
    fi

    # Check if download script exists
    if [ -f "download_models.py" ]; then
        print_success "download_models.py found"
    else
        print_error "download_models.py not found"
        exit 1
    fi
}

# Download default models
download_models() {
    print_section "Downloading Models"

    print_info "This will download the embedding model to ./model_cache/"
    print_info "Models will be reused across container restarts"

    # Download the default embedding model
    echo ""
    print_info "Downloading default embedding model..."
    uv run python download_models.py

    # Show cache status
    echo ""
    print_info "Checking cache status..."
    uv run python download_models.py list
}

# Setup Docker volumes
setup_docker() {
    print_section "Docker Setup"

    # Create model cache directory if it doesn't exist
    if [ ! -d "./model_cache" ]; then
        mkdir -p ./model_cache
        print_success "Created ./model_cache directory"
    else
        print_success "Model cache directory exists"
    fi

    print_info "Docker volumes configured:"
    echo "  📁 ./model_cache → /app/model_cache"
    echo "  📁 ./chroma_db → /app/chroma_db"
    echo "  📁 ./documents → /app/documents"
}

# Verify setup
verify_setup() {
    print_section "Verification"

    # Check cache size
    cache_size=$(uv run python download_models.py size 2>/dev/null || echo "Unknown")
    print_success "Cache ready: $cache_size"

    # List cached models
    echo ""
    print_info "Cached models:"
    uv run python download_models.py list 2>/dev/null || echo "  None"
}

# Show next steps
show_next_steps() {
    print_section "Next Steps"

    echo "🚀 Ready to run Docker!"
    echo ""
    echo "Development mode:"
    echo "  docker-compose -f docker-compose.dev.yml up"
    echo ""
    echo "Production mode:"
    echo "  docker-compose up"
    echo ""
    echo "🎯 Benefits:"
    echo "  ✅ Faster container startup (no model downloads)"
    echo "  ✅ Offline capability"
    echo "  ✅ Bandwidth savings"
    echo "  ✅ Consistent model versions"
    echo ""
    echo "📚 Model management:"
    echo "  uv run python download_models.py list         # List models"
    echo "  uv run python download_models.py size         # Check cache size"
    echo "  uv run python download_models.py download --model MODEL_NAME  # Download specific model"
    echo "  uv run python download_models.py clear        # Clear cache"
}

# Main execution
main() {
    local action="${1:-setup}"

    print_header

    case $action in
        "setup")
            check_requirements
            download_models
            setup_docker
            verify_setup
            show_next_steps
            ;;
        "download")
            if [ -z "$2" ]; then
                print_error "Please specify a model: $0 download MODEL_NAME"
                exit 1
            fi
            check_requirements
            print_section "Downloading Custom Model"
            uv run python download_models.py download --model "$2"
            ;;
        "list")
            check_requirements
            uv run python download_models.py list
            ;;
        "size")
            check_requirements
            uv run python download_models.py size
            ;;
        "clear")
            check_requirements
            print_section "Clearing Cache"
            uv run python download_models.py clear
            ;;
        "verify")
            check_requirements
            verify_setup
            ;;
        "help"|"-h"|"--help")
            echo "Model Cache Setup Script"
            echo ""
            echo "Usage: $0 [setup|download|list|size|clear|verify|help]"
            echo ""
            echo "Commands:"
            echo "  setup              - Full setup (download models, configure Docker)"
            echo "  download MODEL     - Download specific model"
            echo "  list               - List cached models"
            echo "  size               - Show cache size"
            echo "  clear              - Clear cache"
            echo "  verify             - Verify setup"
            echo "  help               - Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 setup                                    # Initial setup"
            echo "  $0 download sentence-transformers/all-MiniLM-L6-v2  # Download specific model"
            echo "  $0 list                                     # List models"
            ;;
        *)
            print_error "Unknown command: $action"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"