#!/bin/bash
# Quick Docker validation script - validates setup without building
# Use this to check if everything is ready before running the full test

set -e

echo "🔍 Docker Setup Validation"
echo "=========================="
echo ""

ERRORS=0

# Colors
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[0;33m'
    NC='\033[0m'
else
    GREEN=''; RED=''; YELLOW=''; NC=''
fi

print_check() {
    echo -n "Checking $1... "
}

print_ok() {
    echo -e "${GREEN}OK${NC}"
}

print_fail() {
    echo -e "${RED}FAILED${NC}"
    ((ERRORS++))
}

print_warn() {
    echo -e "${YELLOW}WARNING${NC}"
}

# Check 1: Docker installation
print_check "Docker installation"
if command -v docker &> /dev/null; then
    print_ok
    echo "  Version: $(docker --version)"
else
    print_fail
    echo "  Docker is not installed. Install from: https://docs.docker.com/get-docker/"
fi

# Check 2: Docker daemon
print_check "Docker daemon"
if docker info &> /dev/null 2>&1; then
    print_ok
else
    print_fail
    echo "  Docker daemon is not running. Start Docker Desktop or service."
fi

# Check 3: Dockerfile exists
print_check "Dockerfile"
if [ -f "Dockerfile" ]; then
    print_ok
    echo "  Path: $(pwd)/Dockerfile"
else
    print_fail
    echo "  Dockerfile not found in current directory"
fi

# Check 4: docker-entrypoint.sh
print_check "docker-entrypoint.sh"
if [ -f "docker-entrypoint.sh" ]; then
    if [ -x "docker-entrypoint.sh" ]; then
        print_ok
    else
        print_warn
        echo "  File exists but is not executable. Run: chmod +x docker-entrypoint.sh"
    fi
else
    print_fail
    echo "  docker-entrypoint.sh not found"
fi

# Check 5: docker-compose.yml
print_check "docker-compose.yml"
if [ -f "docker-compose.yml" ]; then
    print_ok
else
    print_warn
    echo "  docker-compose.yml not found (optional)"
fi

# Check 6: Python dependencies file
print_check "requirements.txt"
if [ -f "requirements.txt" ]; then
    print_ok
    echo "  Dependencies: $(wc -l < requirements.txt | tr -d ' ') packages"
else
    print_fail
    echo "  requirements.txt not found"
fi

# Check 7: Application code
print_check "Application code"
if [ -d "discovery" ] && [ -f "cli.py" ]; then
    print_ok
    echo "  discovery/ directory and cli.py found"
else
    print_fail
    echo "  Missing discovery/ directory or cli.py"
fi

# Check 8: Docker Compose (optional)
print_check "docker-compose command"
if command -v docker-compose &> /dev/null; then
    print_ok
    echo "  Version: $(docker-compose --version)"
else
    print_warn
    echo "  docker-compose not installed (optional, use 'docker compose' instead)"
fi

# Check 9: Python3 (for JSON validation)
print_check "Python3"
if command -v python3 &> /dev/null; then
    print_ok
    echo "  Version: $(python3 --version)"
else
    print_warn
    echo "  Python3 not found (needed for JSON validation in tests)"
fi

# Check 10: Disk space
print_check "Disk space"
if command -v df &> /dev/null; then
    AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
    echo -e "${GREEN}OK${NC}"
    echo "  Available: $AVAILABLE (need ~2GB for build)"
else
    print_warn
    echo "  Could not check disk space"
fi

# Summary
echo ""
echo "=========================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All required checks passed${NC}"
    echo ""
    echo "You're ready to build and test:"
    echo "  ./test-docker-improved.sh"
    echo ""
    echo "Or build manually:"
    echo "  docker build -t surface-discovery ."
else
    echo -e "${RED}✗ $ERRORS check(s) failed${NC}"
    echo ""
    echo "Fix the issues above before building."
    exit 1
fi
