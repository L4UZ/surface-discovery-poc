# Surface Discovery

In-depth web attack surface discovery service for AI-powered pentesting.

## Overview

Surface Discovery performs comprehensive reconnaissance on web targets, gathering intelligence across multiple layers:
- **Domain & Infrastructure**: Subdomain enumeration, DNS mapping, WHOIS data, port scanning
- **Service & Technology**: Live service detection, technology fingerprinting, security headers
- **Web Application**: Endpoint discovery, API mapping, form detection
- **Intelligence & Enrichment**: CVE mapping, risk scoring, pentest recommendations

## Features

### Discovery Pipeline Stages

1. **Stage 1: Passive Discovery** - Subdomain enumeration via subfinder
2. **Stage 1.5: Port Discovery** - Network port scanning with naabu (NEW)
   - Depth-based scanning: shallow (100 ports), normal (1000 ports), deep (all 65535 ports)
   - Configurable scan rate and timeouts
   - Automatic service detection
3. **Stage 2: Active Discovery** - HTTP/HTTPS probing and technology detection
4. **Stage 3: Deep Discovery** - Web crawling and endpoint enumeration
5. **Stage 4: Enrichment** - Infrastructure intelligence (cloud providers, CDN, ASN)
6. **Stage 5: Vulnerability Scanning** - Template-based security scanning with nuclei

## Installation

### Option 1: Docker (Recommended)

**Fastest and easiest** - all dependencies bundled in a single container:

```bash
# Build the image
docker build -t surface-discovery .

# Run discovery (basic - without port scanning)
docker run --rm -v $(pwd)/results:/output surface-discovery example.com

# Run with port scanning (requires network capabilities)
docker run --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/results:/output \
  surface-discovery example.com

# With options
docker run --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/results:/output \
  surface-discovery example.com --depth deep --verbose
```

**Note:** Port scanning requires `--cap-add=NET_RAW` and `--cap-add=NET_ADMIN` flags for raw socket access. Without these flags, Stage 1.5 (Port Discovery) will be skipped.

### Authenticated Scanning

For scanning protected areas with authentication:

```bash
docker run --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  -e API_TOKEN -e SESSION_ID \
  surface-discovery example.com \
  --auth-mode \
  --auth-config /input/auth-config.yaml
```

See [docs/AUTHENTICATED_SCAN.md](docs/AUTHENTICATED_SCAN.md) for complete authentication guide.

### Documentation

- [Docker Usage](DOCKER.md) - Complete Docker documentation
- [Authenticated Scanning](docs/AUTHENTICATED_SCAN.md) - Authentication configuration guide
- [Example Auth Config](input/strike-auth.yaml) - Authentication file template

### Option 2: Local Installation

#### Prerequisites

Install required external tools:

```bash
# Install Go-based security tools
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
```

#### Python Environment

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies and create virtual environment
uv sync

# Activate the virtual environment (manual method)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or use direnv for automatic activation (recommended)
brew install direnv  # macOS, or: sudo apt install direnv (Linux)
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc && source ~/.zshrc
direnv allow .
# Now the venv activates automatically when you cd into the directory!
```

## Usage

### Docker Usage

Basic discovery (without port scanning):
```bash
docker run --rm -v $(pwd)/results:/output surface-discovery example.com
```

With port scanning enabled:
```bash
docker run --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/results:/output \
  surface-discovery example.com
```

Advanced options:
```bash
docker run --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/results:/output \
  surface-discovery example.com \
  --depth deep \
  --timeout 900 \
  --parallel 15 \
  --verbose
```

Using docker-compose (with port scanning):
```bash
docker-compose run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  surface-discovery example.com --depth deep
```

### Local Usage

Basic discovery:
```bash
uv run python cli.py --url https://example.com --output results.json
```

Advanced options:
```bash
uv run python cli.py \
  --url https://example.com \
  --output results.json \
  --depth deep \
  --timeout 900 \
  --parallel 10 \
  --verbose
```

## Output

Results are saved as structured JSON containing:
- Discovered subdomains and DNS records
- **Open ports and services** (per subdomain/host)
- Live services and technology stack
- Web endpoints and API paths
- Security findings and CVE mappings
- Pentest focus recommendations
- **Statistics**: total ports scanned, open ports found, hosts with open ports

## Architecture

```
discovery/
├── core.py              # Main orchestration engine
├── stages/              # Discovery pipeline stages
│   ├── passive.py       # Stage 1: Passive reconnaissance
│   ├── port_discovery.py # Stage 1.5: Port scanning (NEW)
│   ├── active.py        # Stage 2: Active probing
│   ├── deep.py          # Stage 3: Deep crawling
│   ├── enrichment.py    # Stage 4: Analysis & CVE mapping
│   └── vulnerability.py # Stage 5: Security scanning
├── tools/               # Tool integration
│   ├── runner.py        # Subprocess execution (includes naabu)
│   └── parsers.py       # Output parsing
├── models/              # Pydantic data models
│   ├── domain.py        # Domain/subdomain models (includes PortScanResult)
│   └── discovery.py     # Main result and statistics models
└── utils/               # Logging, progress, helpers
```

## Development

Run tests:
```bash
uv run pytest tests/
```

Format code:
```bash
uv run black discovery/ tests/
```

Type checking:
```bash
uv run mypy discovery/
```

## License

MIT
