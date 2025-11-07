#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting cleanup...${NC}\n"

# Clean Python bytecode cache (__pycache__ and .pyc files)
echo -e "${GREEN}→${NC} Cleaning Python bytecode cache..."
PYCACHE_COUNT=$(find . -type d -name "__pycache__" | wc -l | tr -d ' ')
PYC_COUNT=$(find . -type f -name "*.pyc" | wc -l | tr -d ' ')

if [ "$PYCACHE_COUNT" -gt 0 ] || [ "$PYC_COUNT" -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    echo -e "  Removed ${PYCACHE_COUNT} __pycache__ directories and ${PYC_COUNT} .pyc files"
else
    echo -e "  No Python bytecode cache found"
fi

# Clean pytest cache
echo -e "${GREEN}→${NC} Cleaning pytest cache..."
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache
    echo -e "  Removed .pytest_cache"
else
    echo -e "  No pytest cache found"
fi

# Clean UV cache (optional - uncomment if needed)
# echo -e "${GREEN}→${NC} Cleaning UV package cache..."
# uv cache clean
# echo -e "  UV cache cleaned"

# Clean build artifacts
echo -e "${GREEN}→${NC} Cleaning build artifacts..."
BUILD_ARTIFACTS=0
if [ -d "build" ]; then
    rm -rf build
    BUILD_ARTIFACTS=$((BUILD_ARTIFACTS + 1))
fi
if [ -d "dist" ]; then
    rm -rf dist
    BUILD_ARTIFACTS=$((BUILD_ARTIFACTS + 1))
fi
if [ -d "*.egg-info" ]; then
    rm -rf *.egg-info
    BUILD_ARTIFACTS=$((BUILD_ARTIFACTS + 1))
fi

if [ "$BUILD_ARTIFACTS" -gt 0 ]; then
    echo -e "  Removed build artifacts"
else
    echo -e "  No build artifacts found"
fi

# Clean coverage reports
echo -e "${GREEN}→${NC} Cleaning coverage reports..."
if [ -f ".coverage" ] || [ -d "htmlcov" ]; then
    rm -f .coverage
    rm -rf htmlcov
    echo -e "  Removed coverage reports"
else
    echo -e "  No coverage reports found"
fi

echo -e "\n${GREEN}✓${NC} Cleanup complete!"
