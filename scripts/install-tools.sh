#!/usr/bin/env bash
set -e

# Surface Discovery - External Tools Installation Script
# Installs all required Go-based security tools from ProjectDiscovery

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logo
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════╗
║                                                   ║
║         Surface Discovery - Tool Installer        ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo -e "${RED}✗ Go is not installed${NC}"
    echo ""
    echo "Please install Go first:"
    echo "  macOS:   brew install go"
    echo "  Linux:   sudo apt-get install golang-go"
    echo "  Windows: Download from https://go.dev/dl/"
    exit 1
fi

echo -e "${GREEN}✓ Go is installed: $(go version)${NC}"
echo ""

# Ensure ~/go/bin is in PATH
if [[ ":$PATH:" != *":$HOME/go/bin:"* ]]; then
    echo -e "${YELLOW}⚠ Adding ~/go/bin to PATH for this session${NC}"
    export PATH=$PATH:$HOME/go/bin

    echo ""
    echo -e "${YELLOW}Add this to your shell config (~/.bashrc, ~/.zshrc, etc.):${NC}"
    echo "  export PATH=\$PATH:\$HOME/go/bin"
    echo ""
fi

# ProjectDiscovery tools to install (tool:package format)
TOOLS=(
    "subfinder:github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
    "httpx:github.com/projectdiscovery/httpx/cmd/httpx@latest"
    "nuclei:github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest"
    "katana:github.com/projectdiscovery/katana/cmd/katana@latest"
    "dnsx:github.com/projectdiscovery/dnsx/cmd/dnsx@latest"
    "naabu:github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"
)

# Installation counters
INSTALLED=0
FAILED=0
SKIPPED=0

echo "Installing ProjectDiscovery tools..."
echo ""

for entry in "${TOOLS[@]}"; do
    tool="${entry%%:*}"
    package="${entry#*:}"

    # Check if already installed
    if command -v "$tool" &> /dev/null; then
        echo -e "${BLUE}ℹ $tool is already installed ($(which $tool))${NC}"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo -e "${YELLOW}⏳ Installing $tool...${NC}"

    if go install -v "$package"; then
        echo -e "${GREEN}✓ $tool installed successfully${NC}"
        INSTALLED=$((INSTALLED + 1))
    else
        echo -e "${RED}✗ Failed to install $tool${NC}"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

# Set capabilities for naabu (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]] && command -v naabu &> /dev/null; then
    echo ""
    echo -e "${YELLOW}Setting network capabilities for naabu (requires sudo)...${NC}"

    NAABU_PATH=$(which naabu)
    if sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip "$NAABU_PATH" 2>/dev/null; then
        echo -e "${GREEN}✓ Network capabilities set for naabu${NC}"
    else
        echo -e "${YELLOW}⚠ Could not set capabilities (may need to run naabu with sudo)${NC}"
    fi
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════"
echo -e "${GREEN}Installation Summary:${NC}"
echo "  Installed: $INSTALLED"
echo "  Skipped:   $SKIPPED (already installed)"
echo "  Failed:    $FAILED"
echo "═══════════════════════════════════════════════════"

# Verification
echo ""
echo "Verifying installations..."
echo ""

ALL_GOOD=true
for entry in "${TOOLS[@]}"; do
    tool="${entry%%:*}"
    if command -v "$tool" &> /dev/null; then
        VERSION=$($tool -version 2>/dev/null || $tool --version 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✓ $tool${NC} - $VERSION"
    else
        echo -e "${RED}✗ $tool not found${NC}"
        ALL_GOOD=false
    fi
done

echo ""

if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✅ All tools installed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Install Node.js dependencies: pnpm install"
    echo "  2. Build TypeScript: pnpm run build"
    echo "  3. Verify installation: pnpm dev --check-tools"
    echo "  4. Run discovery: pnpm dev --url example.com"
    echo ""
    echo "Or use Docker:"
    echo "  docker build -t surface-discovery ."
    echo "  docker run surface-discovery --url example.com"
    exit 0
else
    echo -e "${RED}⚠ Some tools failed to install${NC}"
    echo ""
    echo "Try manually installing failed tools:"
    echo "  go install -v <package-url>@latest"
    exit 1
fi
