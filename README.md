# Surface Discovery

In-depth web attack surface discovery service for AI-powered pentesting.

## Overview

Surface Discovery performs comprehensive reconnaissance on web targets, gathering intelligence across multiple layers:
- **Domain & Infrastructure**: Subdomain enumeration, DNS mapping, WHOIS data
- **Service & Technology**: Live service detection, technology fingerprinting, security headers
- **Web Application**: Endpoint discovery, API mapping, form detection
- **Intelligence & Enrichment**: CVE mapping, risk scoring, pentest recommendations

## Installation

### Option 1: Docker (Recommended)

**Fastest and easiest** - all dependencies bundled in a single container:

```bash
# Build the image
docker build -t surface-discovery .

# Run discovery
docker run --rm -v $(pwd)/results:/output surface-discovery example.com

# With options
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com --depth deep --verbose
```

See [DOCKER.md](DOCKER.md) for complete Docker documentation.

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
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Docker Usage

Basic discovery:
```bash
docker run --rm -v $(pwd)/results:/output surface-discovery example.com
```

Advanced options:
```bash
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com \
  --depth deep \
  --timeout 900 \
  --parallel 15 \
  --verbose
```

Using docker-compose:
```bash
docker-compose run --rm surface-discovery example.com --depth deep
```

### Local Usage

Basic discovery:
```bash
python cli.py --url https://example.com --output results.json
```

Advanced options:
```bash
python cli.py \
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
- Live services and technology stack
- Web endpoints and API paths
- Security findings and CVE mappings
- Pentest focus recommendations

## Architecture

```
discovery/
├── core.py           # Main orchestration engine
├── stages/           # Discovery pipeline stages
│   ├── passive.py    # Passive reconnaissance
│   ├── active.py     # Active probing
│   ├── deep.py       # Deep crawling
│   └── enrichment.py # Analysis & CVE mapping
├── tools/            # Tool integration
│   ├── runner.py     # Subprocess execution
│   └── parsers.py    # Output parsing
├── models/           # Pydantic data models
└── utils/            # Logging, progress, helpers
```

## Development

Run tests:
```bash
pytest tests/
```

Format code:
```bash
black discovery/ tests/
```

Type checking:
```bash
mypy discovery/
```

## License

MIT
