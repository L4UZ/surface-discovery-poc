# Complete Installation & Setup Guide

## Quick Start (3 Steps)

```bash
# 1. Install external security tools
./scripts/install-tools.sh

# 2. Install Node.js dependencies
pnpm install

# 3. Verify installation
pnpm dev --check-tools
```

Done! Your environment is ready.

---

## Part 1: External Tools Installation

### Automated Installation (Recommended)

```bash
./scripts/install-tools.sh
```

This installs all required ProjectDiscovery tools:
- **subfinder** - Subdomain enumeration
- **httpx** - HTTP probing
- **naabu** - Port scanning
- **katana** - Web crawling
- **dnsx** - DNS resolution

### Requirements

- **Go 1.20+** must be installed
- **macOS**: Script auto-detects Homebrew bash
- **Linux**: Works with system bash

### Manual Installation (Alternative)

If you prefer manual installation:

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

# Add to PATH
export PATH=$PATH:$HOME/go/bin
```

---

## Part 2: Node.js Environment Setup

### Prerequisites

- **Node.js 20+** - [Download](https://nodejs.org/)
- **pnpm** - Fast package manager

### Install pnpm

```bash
# Using npm (one-time)
npm install -g pnpm

# Or using Homebrew (macOS)
brew install pnpm

# Or using Corepack (Node.js 16.13+)
corepack enable
corepack prepare pnpm@latest --activate
```

### Install Dependencies

```bash
# Install all project dependencies
pnpm install
```

### Benefits of pnpm:
- ⚡ 2-3x faster than npm
- 💾 Efficient disk space usage (hardlinks)
- 🔒 Strict dependency resolution
- 📦 Monorepo-friendly

---

## Part 3: Verification

### Check Tool Installation

```bash
pnpm dev --check-tools
```

Expected output:
```
Checking external tools installation...
✓ subfinder (v2.6.3)
✓ httpx (v1.3.7)
✓ katana (v1.0.4)
✓ dnsx (v1.1.6)
✓ naabu (v2.2.0)

All required tools are installed!
```

### Check TypeScript Build

```bash
# Type check
pnpm typecheck

# Build
pnpm build
```

### Run Test Scan

```bash
# Quick test
pnpm dev --url example.com --depth shallow
```

---

## Part 4: Development Setup

### Code Quality Tools

The project includes:
- **TypeScript** - Type-safe JavaScript
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **Vitest** - Unit testing

### Common Commands

```bash
# Development (with hot reload)
pnpm dev --url example.com

# Production build
pnpm build
pnpm start -- --url example.com

# Code quality
pnpm typecheck  # Type checking
pnpm lint       # Check for issues
pnpm lint:fix   # Auto-fix issues
pnpm format     # Format code
pnpm format:check # Check formatting

# Testing
pnpm test           # Run tests
pnpm test:coverage  # With coverage
pnpm test:watch     # Watch mode
```

---

## Part 5: Docker Installation (Optional)

### Prerequisites

- **Docker** - [Get Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (usually bundled with Docker)

### Build Docker Image

```bash
docker build -t surface-discovery .
```

### Run with Docker

```bash
# Basic scan
docker run --rm \
  -v $(pwd)/results:/output \
  surface-discovery --url example.com

# With port scanning (requires capabilities)
docker run --rm \
  --cap-add=NET_RAW \
  --cap-add=NET_ADMIN \
  -v $(pwd)/results:/output \
  surface-discovery --url example.com
```

### Using Docker Compose

```bash
# Run scan
docker-compose run --rm surface-discovery --url example.com

# With port scanning
docker-compose run --rm \
  --cap-add=NET_RAW \
  --cap-add=NET_ADMIN \
  surface-discovery --url example.com --depth deep
```

---

## Troubleshooting

### Issue: Tools not found

**Problem**: `pnpm dev --check-tools` shows missing tools

**Solution**:
```bash
# Reinstall tools
./scripts/install-tools.sh

# Check Go bin in PATH
echo $PATH | grep go/bin

# If not in PATH, add it
export PATH=$PATH:$HOME/go/bin

# Make permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.zshrc
source ~/.zshrc
```

### Issue: pnpm not found

**Problem**: `command not found: pnpm`

**Solution**:
```bash
# Install pnpm globally
npm install -g pnpm

# Or use Corepack
corepack enable
```

### Issue: Node.js version too old

**Problem**: `Requires Node.js 20+`

**Solution**:
```bash
# Install Node.js 20+ from nodejs.org
# Or use nvm
nvm install 20
nvm use 20
```

### Issue: TypeScript build errors

**Problem**: `pnpm build` fails

**Solution**:
```bash
# Clean and rebuild
rm -rf dist/ node_modules/
pnpm install
pnpm build

# Check for type errors
pnpm typecheck
```

### Issue: Port scanning fails

**Problem**: `naabu: permission denied`

**Solution**:

**Local (Linux)**:
```bash
# Give naabu raw socket capabilities
sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip $(which naabu)
```

**Docker**:
```bash
# Use capabilities flags
docker run --cap-add=NET_RAW --cap-add=NET_ADMIN ...
```

### Issue: Permission errors on output

**Problem**: Cannot write results to output directory

**Solution**:
```bash
# Create output directory
mkdir -p output results

# Fix permissions
chmod 755 output results

# Docker: Use current user
docker run --user $(id -u):$(id -g) ...
```

---

## Advanced Configuration

### Custom Tool Paths

If tools are installed in non-standard locations:

```bash
# Set tool paths in environment
export SUBFINDER_PATH=/custom/path/subfinder
export HTTPX_PATH=/custom/path/httpx
export NAABU_PATH=/custom/path/naabu
export KATANA_PATH=/custom/path/katana
export DNSX_PATH=/custom/path/dnsx
```

### Performance Tuning

```bash
# Increase parallelism (if system supports it)
pnpm start -- --url example.com --parallel 20

# Longer timeout for large scans
pnpm start -- --url example.com --timeout 3600

# Custom depth configuration
pnpm start -- --url example.com --depth deep
```

### Development with TypeScript Watch Mode

```bash
# Terminal 1: Watch TypeScript
pnpm build --watch

# Terminal 2: Run with nodemon
npx nodemon dist/cli.js --url example.com
```

---

## Platform-Specific Notes

### macOS

- **Homebrew** recommended for Go installation
- **Rosetta 2** required for Apple Silicon (M1/M2) if using non-ARM binaries
- **Gatekeeper** may block unsigned binaries - run `xattr -d com.apple.quarantine $(which naabu)` if needed

### Linux

- **apt/yum** can install Go: `sudo apt install golang-go`
- **setcap** required for naabu port scanning capabilities
- **SELinux** may block raw sockets - temporarily disable with `sudo setenforce 0` (for testing only)

### Windows (WSL2 Required)

- **WSL2** (Windows Subsystem for Linux) required
- Follow Linux installation steps inside WSL2
- Docker Desktop with WSL2 backend recommended

---

## Next Steps

Once installed:

1. **Quick Test**: `pnpm dev --url example.com --depth shallow`
2. **Read Quick Start**: See [QUICKSTART.md](./QUICKSTART.md)
3. **Review CLI Options**: See [README.md](../README.md)
4. **Configure Authentication**: See [AUTHENTICATED_SCAN.md](./AUTHENTICATED_SCAN.md)
5. **Docker Usage**: See [DOCKER.md](./DOCKER.md)

---

## Uninstallation

### Remove Node.js Dependencies

```bash
rm -rf node_modules/
```

### Remove External Tools

```bash
rm -f ~/go/bin/{subfinder,httpx,naabu,katana,dnsx}
```

### Remove Build Artifacts

```bash
rm -rf dist/ output/ results/
```
