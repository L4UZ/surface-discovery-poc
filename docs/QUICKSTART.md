# Quick Start Guide

Get started with Surface Discovery in 5 minutes.

## Prerequisites

- **Node.js 20+** - JavaScript runtime
- **pnpm** - Fast package manager (`npm install -g pnpm`)
- **External Tools** - ProjectDiscovery security tools

## Installation

### 1. Install External Tools

```bash
# Automated installation (recommended)
./scripts/install-tools.sh
```

This installs:
- subfinder (subdomain enumeration)
- httpx (HTTP probing)
- naabu (port scanning)
- katana (web crawling)
- dnsx (DNS resolution)

### 2. Install Node.js Dependencies

```bash
pnpm install
```

### 3. Verify Installation

```bash
pnpm dev --check-tools
```

You should see all 5 tools detected:
```
✓ subfinder
✓ httpx
✓ katana
✓ dnsx
✓ naabu
```

## Basic Usage

### Development Mode (Quick Testing)

```bash
# Basic scan
pnpm dev --url https://example.com

# Shallow scan (faster, less comprehensive)
pnpm dev --url https://example.com --depth shallow

# Deep scan (slower, more comprehensive)
pnpm dev --url https://example.com --depth deep --verbose
```

### Production Mode

```bash
# Build TypeScript to JavaScript
pnpm build

# Run discovery
pnpm start -- --url https://example.com --output results.json
```

## Common Use Cases

### Quick Reconnaissance

For rapid initial assessment (30-60 seconds):

```bash
pnpm dev --url https://target.com --depth shallow
```

This performs:
- Subdomain enumeration (limit: 20)
- Port scanning (top 100 ports)
- HTTP probing
- Basic crawling (depth: 2)

### Standard Discovery

For balanced coverage (3-10 minutes):

```bash
pnpm dev --url https://target.com --depth normal --verbose
```

This performs:
- Full subdomain enumeration
- Port scanning (top 1000 ports)
- HTTP probing with technology detection
- Web crawling (depth: 3)
- Infrastructure intelligence

### Comprehensive Discovery

For thorough reconnaissance (10-15 minutes):

```bash
pnpm dev --url https://target.com --depth deep --verbose --timeout 900
```

This performs:
- Unlimited subdomain enumeration
- Full port scan (all 65535 ports)
- HTTP probing with full headers
- Deep web crawling (depth: 5)
- Complete infrastructure analysis

## Docker Usage

### Quick Docker Run

```bash
# Build image (one-time)
docker build -t surface-discovery .

# Run scan
docker run --rm \
  -v $(pwd)/results:/output \
  surface-discovery --url example.com
```

### With Port Scanning

Port scanning requires elevated network capabilities:

```bash
docker run --rm \
  --cap-add=NET_RAW \
  --cap-add=NET_ADMIN \
  -v $(pwd)/results:/output \
  surface-discovery --url example.com --depth deep
```

## Understanding Output

Discovery results are saved as JSON files with:

### Metadata
```json
{
  "metadata": {
    "target": "example.com",
    "scanId": "uuid",
    "startTime": "2024-01-01T00:00:00Z",
    "durationSeconds": 180,
    "status": "completed"
  }
}
```

### Domains & Subdomains
```json
{
  "domains": {
    "rootDomain": "example.com",
    "subdomains": [
      {
        "name": "api.example.com",
        "ips": ["1.2.3.4"],
        "status": "live",
        "openPorts": [80, 443]
      }
    ]
  }
}
```

### Services
```json
{
  "services": [
    {
      "url": "https://api.example.com",
      "statusCode": 200,
      "technologies": [
        {"name": "nginx", "version": "1.21.0"}
      ]
    }
  ]
}
```

### Endpoints
```json
{
  "endpoints": [
    {
      "url": "https://api.example.com/api/users",
      "method": "GET",
      "discoveredVia": "crawl"
    }
  ]
}
```

## Development Workflow

### Check Code Quality

```bash
# Type check
pnpm typecheck

# Lint code
pnpm lint

# Format code
pnpm format
```

### Run Tests

```bash
# Run all tests
pnpm test

# Run with coverage
pnpm test:coverage

# Watch mode (during development)
pnpm test:watch
```

## CLI Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--url <url>` | Target URL (required) | - |
| `--output <path>` | Output file path | Auto-generated |
| `--depth <level>` | shallow\|normal\|deep | normal |
| `--timeout <seconds>` | Max execution time | 1800 |
| `--parallel <number>` | Concurrent operations | 10 |
| `--verbose` | Enable verbose logging | false |
| `--check-tools` | Verify tool installation | - |
| `--auth-mode` | Enable authenticated scan | false |
| `--auth-config <path>` | Auth config JSON file | - |

## Troubleshooting

### Tools Not Found

If `--check-tools` shows missing tools:

```bash
# Reinstall tools
./scripts/install-tools.sh

# Verify PATH
echo $PATH | grep -q go/bin && echo "Go bin in PATH" || echo "Add ~/go/bin to PATH"
```

### Build Errors

```bash
# Clean build
rm -rf dist/
pnpm build

# Check TypeScript
pnpm typecheck
```

### Port Scanning Fails

Port scanning requires elevated privileges:

```bash
# Local: Run as root (not recommended)
sudo pnpm start -- --url example.com

# Docker: Use capabilities flags
docker run --cap-add=NET_RAW --cap-add=NET_ADMIN ...
```

## Next Steps

- **Authentication**: See [AUTHENTICATED_SCAN.md](./AUTHENTICATED_SCAN.md) for authenticated scanning
- **Docker**: See [DOCKER.md](./DOCKER.md) for advanced Docker usage
- **Installation**: See [INSTALLATION.md](./INSTALLATION.md) for detailed setup

## Performance Tips

1. **Adjust Depth**: Use `shallow` for quick checks, `deep` for thorough scans
2. **Increase Parallelism**: Use `--parallel 15` for faster scans (if system supports it)
3. **Set Timeouts**: Use `--timeout 600` to limit long-running scans
4. **Filter Subdomains**: Focus on specific subdomains if too many are discovered

## Common Patterns

### CI/CD Integration

```bash
#!/bin/bash
pnpm build
pnpm start -- \
  --url https://staging.example.com \
  --depth shallow \
  --output ci-scan-$(date +%Y%m%d).json
```

### Scheduled Scans

```bash
# Cron: Daily deep scan at 2 AM
0 2 * * * cd /path/to/surface-discovery && pnpm start -- --url target.com --depth deep
```

### Multiple Targets

```bash
#!/bin/bash
TARGETS=("example.com" "test.com" "demo.com")
for target in "${TARGETS[@]}"; do
  pnpm start -- --url "https://$target" --output "$target-$(date +%Y%m%d).json"
done
```
