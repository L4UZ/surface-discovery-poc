#!/bin/bash
# Docker build and test script for Surface Discovery
# Improved version with better error handling and compatibility

# Exit on error, but with custom error handling
set -o errexit
set -o pipefail
set -o nounset

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🐳 Surface Discovery Docker Build & Test"
echo "=========================================="
echo "Script directory: $SCRIPT_DIR"
echo ""

# Colors (with fallback for non-color terminals)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    YELLOW='\033[0;33m'
    RED='\033[0;31m'
    NC='\033[0m'
else
    GREEN=''
    BLUE=''
    YELLOW=''
    RED=''
    NC=''
fi

# Configuration
IMAGE_NAME="surface-discovery"
TEST_TARGET="strike.sh"
RESULTS_DIR="./results"
TEST_TIMEOUT=300  # 5 minutes for test
BUILD_TIMEOUT=600 # 10 minutes for build

# Error counter
ERRORS=0

# Functions
print_step() {
    echo -e "\n${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((ERRORS++))
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo "$1"
}

# Prerequisites check
check_prerequisites() {
    print_step "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        return 1
    fi
    print_success "Docker found: $(docker --version)"

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon not running. Please start Docker."
        return 1
    fi
    print_success "Docker daemon running"

    # Check Python3 (for JSON validation)
    if ! command -v python3 &> /dev/null; then
        print_warning "Python3 not found. Skipping JSON validation."
        SKIP_JSON_VALIDATION=true
    else
        print_success "Python3 found: $(python3 --version)"
        SKIP_JSON_VALIDATION=false
    fi

    return 0
}

# Build image
build_image() {
    print_step "Step 1: Building Docker image..."

    # Check if Dockerfile exists
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found in $SCRIPT_DIR"
        return 1
    fi

    # Build with timeout
    print_info "Building image (this may take 5-10 minutes)..."

    if timeout "${BUILD_TIMEOUT}s" docker build -t "$IMAGE_NAME" . 2>&1 | tee build.log; then
        print_success "Build successful"
        rm -f build.log
        return 0
    else
        BUILD_EXIT_CODE=$?
        print_error "Build failed (exit code: $BUILD_EXIT_CODE)"
        print_info "Build log saved to: build.log"
        return 1
    fi
}

# Check image size
check_image_size() {
    print_step "Step 2: Checking image size..."

    if IMAGE_SIZE=$(docker images "$IMAGE_NAME" --format "{{.Size}}" 2>/dev/null); then
        print_info "Image size: $IMAGE_SIZE"
        print_success "Image info retrieved"
        return 0
    else
        print_error "Failed to get image size"
        return 1
    fi
}

# Verify tools
verify_tools() {
    print_step "Step 3: Verifying tools installation..."

    print_info "Running tool check..."

    if docker run --rm "$IMAGE_NAME" --check-tools > tool_check.log 2>&1; then
        print_success "All tools installed"
        cat tool_check.log
        rm -f tool_check.log
        return 0
    else
        print_error "Tool check failed"
        print_info "Tool check log:"
        cat tool_check.log
        rm -f tool_check.log
        return 1
    fi
}

# Test help command
test_help() {
    print_step "Step 4: Testing help command..."

    if docker run --rm "$IMAGE_NAME" --help > /dev/null 2>&1; then
        print_success "Help command works"
        return 0
    else
        print_error "Help command failed"
        return 1
    fi
}

# Test discovery
test_discovery() {
    print_step "Step 5: Testing discovery (shallow mode)..."

    # Create results directory
    mkdir -p "$RESULTS_DIR"
    print_info "Results directory: $SCRIPT_DIR/$RESULTS_DIR"

    # Clean old results
    rm -f "$RESULTS_DIR/discovery_results.json"

    print_info "Running discovery test (timeout: ${TEST_TIMEOUT}s)..."
    print_info "Target: $TEST_TARGET"

    if docker run --rm \
        -v "$SCRIPT_DIR/$RESULTS_DIR:/output" \
        "$IMAGE_NAME" "$TEST_TARGET" \
        --depth shallow \
        --timeout "$TEST_TIMEOUT" 2>&1 | tee discovery_test.log; then
        print_success "Discovery test passed"
        rm -f discovery_test.log
        return 0
    else
        DISCOVERY_EXIT_CODE=$?
        print_error "Discovery test failed (exit code: $DISCOVERY_EXIT_CODE)"
        print_info "Discovery log saved to: discovery_test.log"
        return 1
    fi
}

# Verify output
verify_output() {
    print_step "Step 6: Verifying output file..."

    OUTPUT_FILE="$RESULTS_DIR/discovery_results.json"

    if [ ! -f "$OUTPUT_FILE" ]; then
        print_error "Output file not found: $OUTPUT_FILE"
        print_info "Files in results directory:"
        ls -lah "$RESULTS_DIR" || true
        return 1
    fi

    # Get file size (cross-platform)
    if FILE_SIZE=$(wc -c < "$OUTPUT_FILE" 2>/dev/null); then
        print_info "Output file: $OUTPUT_FILE ($FILE_SIZE bytes)"
    else
        print_warning "Could not determine file size"
    fi

    # Validate JSON if Python3 available
    if [ "$SKIP_JSON_VALIDATION" = false ]; then
        if python3 -m json.tool "$OUTPUT_FILE" > /dev/null 2>&1; then
            print_success "Valid JSON output"
        else
            print_error "Invalid JSON output"
            print_info "First 100 lines of output:"
            head -n 100 "$OUTPUT_FILE"
            return 1
        fi
    else
        print_warning "Skipping JSON validation (Python3 not available)"
    fi

    print_success "Output file verified"
    return 0
}

# Test docker-compose
test_docker_compose() {
    print_step "Step 7: Testing docker-compose..."

    if ! command -v docker-compose &> /dev/null; then
        print_info "Skipping docker-compose test (not installed)"
        return 0
    fi

    if ! [ -f "docker-compose.yml" ]; then
        print_warning "docker-compose.yml not found"
        return 0
    fi

    print_info "Building with docker-compose..."

    if docker-compose build > /dev/null 2>&1; then
        print_success "Docker Compose build successful"
        return 0
    else
        print_warning "Docker Compose build failed (non-critical)"
        return 0  # Don't fail the entire test suite
    fi
}

# Cleanup
cleanup() {
    print_step "Cleanup..."

    # Optional: Remove test results
    # rm -rf "$RESULTS_DIR"

    # Optional: Remove image
    # docker rmi "$IMAGE_NAME" &> /dev/null || true

    print_info "Test artifacts preserved in: $SCRIPT_DIR"
}

# Summary
print_summary() {
    echo ""
    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}=========================================="
        echo "✓ All tests passed!"
        echo "==========================================${NC}"
        echo ""
        echo "Docker image ready to use:"
        echo "  docker run --rm -v \$(pwd)/results:/output $IMAGE_NAME strike.sh"
        echo ""
        echo "Results saved to: $RESULTS_DIR/"
    else
        echo -e "${RED}=========================================="
        echo "✗ Tests failed with $ERRORS error(s)"
        echo "==========================================${NC}"
        echo ""
        echo "Check the logs above for details."
        return 1
    fi
}

# Main execution
main() {
    # Check prerequisites first
    if ! check_prerequisites; then
        print_error "Prerequisites check failed"
        return 1
    fi

    # Run tests (continue on error to collect all failures)
    set +e

    build_image
    check_image_size
    verify_tools
    test_help
    test_discovery
    verify_output
    test_docker_compose

    set -e

    # Cleanup and summary
    cleanup
    print_summary
}

# Run main function
main
EXIT_CODE=$?

exit $EXIT_CODE
