# Surface Discovery

In-depth web attack surface discovery service for AI-powered pentesting.

## Overview

Surface Discovery performs comprehensive reconnaissance on web targets, gathering intelligence across multiple layers:
- **Domain & Infrastructure**: Subdomain enumeration, DNS mapping, WHOIS data, port scanning
- **Service & Technology**: Live service detection, technology fingerprinting, security headers
- **Web Application**: Endpoint discovery, API mapping, form detection
- **Intelligence & Enrichment**: Cloud provider detection, CDN identification, ASN mapping

## Features

### Discovery Pipeline Stages

1. **Stage 1: Passive Discovery** - Subdomain enumeration via subfinder
2. **Stage 1.5: Port Discovery** - Network port scanning with naabu
   - Depth-based scanning: shallow (100 ports), normal (1000 ports), deep (all 65535 ports)
   - Configurable scan rate and timeouts
   - Automatic service detection
3. **Stage 2: Active Discovery** - HTTP/HTTPS probing and technology detection
4. **Stage 3: Deep Discovery** - Web crawling and endpoint enumeration
5. **Stage 4: Enrichment** - Infrastructure intelligence (cloud providers, CDN, ASN)
6. **Stage 5: Authenticated Discovery** - Session-based authenticated crawling

> **Note**: Nuclei vulnerability scanning has been removed from this version.

## Installation

### Prerequisites

- Node.js 20+
- pnpm (`npm install -g pnpm`)
- External security tools (automated installation available)

### Install External Tools

```bash
# Automated installation script
./scripts/install-tools.sh
```

This installs all required ProjectDiscovery tools:
- subfinder (subdomain enumeration)
- httpx (HTTP probing)
- naabu (port scanning)
- katana (web crawling)
- dnsx (DNS resolution)

### Install Node.js Dependencies

```bash
# Install dependencies
pnpm install

# Verify installation
pnpm dev --check-tools
```

## Usage

### Development Mode

```bash
# Basic scan
pnpm dev --url https://example.com

# With options
pnpm dev --url https://example.com --depth deep --verbose
```

### Production Mode

```bash
# Build first
pnpm build

# Run discovery
pnpm start -- --url https://example.com --output results.json
```

### Docker Usage

**Basic discovery (without port scanning):**
```bash
docker build -t surface-discovery .
docker run --rm -v $(pwd)/results:/output surface-discovery --url example.com
```

**With port scanning (requires network capabilities):**
```bash
docker run --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/results:/output \
  surface-discovery --url example.com --depth deep
```

**Note:** Port scanning requires `--cap-add=NET_RAW` and `--cap-add=NET_ADMIN` flags for raw socket access.

### Authenticated Scanning

For scanning protected areas with authentication:

```bash
docker run --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  surface-discovery --url example.com \
  --auth-mode \
  --auth-config /input/auth-config.json
```

See [docs/AUTHENTICATED_SCAN.md](docs/AUTHENTICATED_SCAN.md) for complete authentication guide.

## CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Target URL or domain (required) | - |
| `--output` | Output file path | Auto-generated |
| `--depth` | Discovery depth: shallow\|normal\|deep | normal |
| `--timeout` | Maximum execution time (seconds) | 1800 |
| `--parallel` | Max parallel operations | 10 |
| `--verbose` | Enable verbose logging | false |
| `--check-tools` | Verify external tools installation | - |
| `--auth-mode` | Enable authenticated discovery | false |
| `--auth-config` | JSON authentication configuration file | - |

## Output

Results are saved as structured JSON containing:
- Discovered subdomains and DNS records
- **Open ports and services** (per subdomain/host)
- Live services and technology stack
- Web endpoints and API paths
- Infrastructure intelligence (cloud providers, CDN, ASN)
- **Statistics**: total ports scanned, open ports found, hosts with open ports

## Development

### Code Quality

```bash
# Type checking
pnpm typecheck

# Linting
pnpm lint
pnpm lint:fix

# Formatting
pnpm format
pnpm format:check
```

### Testing

```bash
# Run tests
pnpm test

# Run tests with coverage
pnpm test:coverage
```

## Architecture

```
src/
├── core.ts              # Main orchestration engine
├── stages/              # Discovery pipeline stages
│   ├── passive.ts       # Stage 1: Passive reconnaissance
│   ├── portDiscovery.ts # Stage 1.5: Port scanning
│   ├── active.ts        # Stage 2: Active probing
│   ├── deep.ts          # Stage 3: Deep crawling
│   ├── enrichment.ts    # Stage 4: Infrastructure intelligence
│   └── authenticated.ts # Stage 5: Authenticated discovery
├── tools/               # Tool integration
│   ├── runner.ts        # Subprocess execution
│   └── parsers.ts       # Output parsing
├── models/              # Zod data models
│   ├── domain.ts        # Domain/subdomain models
│   ├── service.ts       # Service detection models
│   ├── url.ts           # URL discovery models
│   ├── auth.ts          # Authentication models
│   └── discovery.ts     # Main result models
├── utils/               # Utilities
│   ├── logger.ts        # Winston logging
│   └── helpers.ts       # Helper functions
└── cli.ts               # Commander.js CLI interface
```

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Installation Guide](docs/INSTALLATION.md)
- [Docker Usage](docs/DOCKER.md)
- [Authenticated Scanning](docs/AUTHENTICATED_SCAN.md)
- [Docker Quick Reference](docs/DOCKER_QUICKREF.md)

## Technology Stack

- **Language**: TypeScript (Node.js 20+)
- **Package Manager**: pnpm
- **Data Validation**: Zod
- **CLI Framework**: Commander.js
- **Logging**: Winston
- **Browser Automation**: Playwright
- **Deployment**: Docker

## License

MIT
