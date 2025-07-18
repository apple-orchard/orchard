#!/bin/bash
"""
Pipeline Testing Helper Script
Runs various tests for the chunking and embedding pipeline.
"""

set -e  # Exit on any error

echo "🧪 CHUNKING & EMBEDDING PIPELINE TESTS"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_section() {
    echo -e "\n${YELLOW}$1${NC}"
    echo "-----------------------------------"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python environment is ready
print_section "Checking Environment"
if command -v uv run python >/dev/null 2>&1; then
    print_success "Python3 found"
else
    print_error "Python3 not found"
    exit 1
fi

# Check if required files exist
if [ -f "test_chunking_embeddings.py" ]; then
    print_success "Test script found"
else
    print_error "test_chunking_embeddings.py not found"
    exit 1
fi

# Function to run a test with error handling
run_test() {
    local test_name="$1"
    local test_command="$2"

    print_section "$test_name"
    if eval "$test_command"; then
        print_success "$test_name completed"
    else
        print_error "$test_name failed"
        return 1
    fi
}

# Main test execution
main() {
    local test_type="${1:-full}"

    case $test_type in
        "quick")
            print_section "Running Quick Semantic Test"
            run_test "Quick Semantic Understanding" "uv run python test_chunking_embeddings.py --quick"
            ;;
        "api")
            print_section "Running API Tests"
            echo "⚠️  Make sure your API is running (python main.py or docker-compose up)"
            read -p "Press Enter to continue when API is ready..."
            run_test "API Endpoint Tests" "uv run python api_test_chunking_embeddings.py"
            ;;
        "full")
            print_section "Running Comprehensive Tests"
            run_test "Full Pipeline Tests" "uv run python test_chunking_embeddings.py"
            ;;
        "file")
            if [ -z "$2" ]; then
                print_error "Please provide a file path: ./test_pipeline.sh file /path/to/your/file"
                exit 1
            fi
            print_section "Testing with Custom File: $2"
            run_test "Custom File Test" "uv run python test_chunking_embeddings.py --file '$2'"
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [quick|api|full|file] [file_path]"
            echo ""
            echo "Options:"
            echo "  quick     - Run only semantic understanding tests"
            echo "  api       - Run API endpoint tests (requires running API)"
            echo "  full      - Run comprehensive test suite (default)"
            echo "  file      - Test with specific file (requires file path)"
            echo "  help      - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 quick                    # Quick semantic test"
            echo "  $0 api                      # API tests"
            echo "  $0 full                     # All tests"
            echo "  $0 file documents/test.pdf  # Test specific file"
            exit 0
            ;;
        *)
            print_error "Unknown test type: $test_type"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac

    print_section "Test Summary"
    print_success "All requested tests completed!"

    if [ "$test_type" = "full" ]; then
        echo ""
        echo "📊 Check the generated test_results_*.json file for detailed results"
        echo "🔍 Review the console output above for any issues"
        echo ""
        echo "Next steps:"
        echo "1. If tests passed: Your pipeline is working correctly!"
        echo "2. If tests failed: Check the TESTING_GUIDE.md for troubleshooting"
        echo "3. For API testing: Run './test_pipeline.sh api'"
    fi
}

# Run main function with all arguments
main "$@"