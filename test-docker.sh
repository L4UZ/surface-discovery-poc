#!/bin/bash
# Docker build and test script for Surface Discovery

set -e

echo "🐳 Surface Discovery Docker Build & Test"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="surface-discovery"
TEST_TARGET="example.com"
RESULTS_DIR="./results"

# Step 1: Build image
echo -e "\n${BLUE}Step 1: Building Docker image...${NC}"
if docker build -t "$IMAGE_NAME" .; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

# Step 2: Check image size
echo -e "\n${BLUE}Step 2: Checking image size...${NC}"
IMAGE_SIZE=$(docker images "$IMAGE_NAME" --format "{{.Size}}")
echo "Image size: $IMAGE_SIZE"

# Step 3: Verify tools installation
echo -e "\n${BLUE}Step 3: Verifying tools installation...${NC}"
if docker run --rm "$IMAGE_NAME" --check-tools; then
    echo -e "${GREEN}✓ All tools installed${NC}"
else
    echo -e "${RED}✗ Tool check failed${NC}"
    exit 1
fi

# Step 4: Test help command
echo -e "\n${BLUE}Step 4: Testing help command...${NC}"
if docker run --rm "$IMAGE_NAME" --help > /dev/null; then
    echo -e "${GREEN}✓ Help command works${NC}"
else
    echo -e "${RED}✗ Help command failed${NC}"
    exit 1
fi

# Step 5: Test discovery (shallow for speed)
echo -e "\n${BLUE}Step 5: Testing discovery (shallow mode)...${NC}"
mkdir -p "$RESULTS_DIR"

if docker run --rm \
    -v "$(pwd)/$RESULTS_DIR:/output" \
    "$IMAGE_NAME" "$TEST_TARGET" \
    --depth shallow \
    --timeout 300; then
    echo -e "${GREEN}✓ Discovery test passed${NC}"
else
    echo -e "${RED}✗ Discovery test failed${NC}"
    exit 1
fi

# Step 6: Verify output file
echo -e "\n${BLUE}Step 6: Verifying output file...${NC}"
OUTPUT_FILE="$RESULTS_DIR/discovery_results.json"

if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
    echo "Output file: $OUTPUT_FILE ($FILE_SIZE bytes)"

    # Check if it's valid JSON
    if python3 -m json.tool "$OUTPUT_FILE" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Valid JSON output${NC}"
    else
        echo -e "${RED}✗ Invalid JSON output${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Output file not found${NC}"
    exit 1
fi

# Step 7: Test docker-compose (if available)
if command -v docker-compose &> /dev/null; then
    echo -e "\n${BLUE}Step 7: Testing docker-compose...${NC}"
    if docker-compose build > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Docker Compose build successful${NC}"
    else
        echo -e "${RED}✗ Docker Compose build failed${NC}"
    fi
else
    echo -e "\n${BLUE}Step 7: Skipping docker-compose test (not installed)${NC}"
fi

# Summary
echo -e "\n${GREEN}=========================================="
echo "✓ All tests passed!"
echo "==========================================${NC}"
echo ""
echo "Docker image ready to use:"
echo "  docker run --rm -v \$(pwd)/results:/output $IMAGE_NAME example.com"
echo ""
echo "Results saved to: $RESULTS_DIR/"
