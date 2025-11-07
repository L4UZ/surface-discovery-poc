# Quick Start Guide

## Installation

### 1. Install External Tools

Use the automated installation script:

```bash
cd surface-discovery
./scripts/install-tools.sh
```

This script will:
- Check if Go is installed
- Install all required ProjectDiscovery tools (subfinder, httpx, nuclei, katana, dnsx, naabu)
- Set up network capabilities for naabu (Linux only)
- Verify all installations
- Add `~/go/bin` to your PATH if needed

### 2. Setup Python Environment

```bash
cd surface-discovery

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies and create virtual environment
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Verify Installation

```bash
uv run python cli.py --check-tools
```

You should see all tools marked as "✓ Installed".

## Basic Usage

### Simple Discovery

```bash
uv run python cli.py --url example.com
```

This will:
- Discover subdomains
- Collect DNS records
- Save results to `discovery_example_com.json`

### Custom Output File

```bash
uv run python cli.py --url example.com --output my_results.json
```

### Deep Discovery

```bash
uv run python cli.py --url example.com --depth deep --verbose
```

This enables:
- More thorough subdomain enumeration
- Extended timeouts
- Detailed logging

## Discovery Depth Levels

| Level | Timeout | Max Subdomains | Crawl Services | Use Case |
|-------|---------|----------------|----------------|----------|
| **shallow** | 5 min | 20 | 3 | Quick reconnaissance |
| **normal** | 10 min | unlimited | 10 | Balanced discovery |
| **deep** | 15 min | unlimited | 20 | Comprehensive analysis |

## Example Commands

### Quick Test
```bash
# Test with example.com (minimal surface)
uv run python cli.py --url example.com --depth shallow
```

### Vulnerable Test Target
```bash
# Test with intentionally vulnerable site (requires permission!)
uv run python cli.py --url testphp.vulnweb.com --depth normal --verbose
```

### Custom Configuration
```bash
# Override specific settings
uv run python cli.py \
  --url example.com \
  --depth normal \
  --timeout 900 \
  --parallel 15 \
  --output results/scan_001.json \
  --verbose
```

## Understanding the Output

The output JSON file contains:

### Metadata
- Scan ID, timestamps, duration
- Tool versions used
- Discovery depth level

### Domains
- Root domain information
- Discovered subdomains with IPs
- DNS records (A, AAAA, MX, TXT, etc.)
- WHOIS data

### Services (planned)
- Live HTTP/HTTPS services
- Technology stack detection
- Security headers analysis

### Findings (planned)
- Security misconfigurations
- Vulnerable components
- Sensitive file exposures

### Recommendations
- Pentest focus areas
- Risk-prioritized targets

## Current Implementation Status

✅ **Implemented (Core Components)**:
- Project structure and configuration
- Subprocess runner for tools
- Pydantic data models
- Tool output parsers
- Passive discovery stage (subdomains, DNS, WHOIS)
- Core orchestration engine
- CLI interface

⏳ **Planned (Future Phases)**:
- Active discovery (HTTP probing, port scanning)
- Deep discovery (web crawling, JS analysis)
- Enrichment (CVE mapping, risk scoring)
- Comprehensive reporting

## Troubleshooting

### "Tool not found" errors

Ensure Go tools are in your PATH:
```bash
which subfinder  # Should show path to binary
export PATH=$PATH:~/go/bin
```

### Python module errors

Sync dependencies with uv:
```bash
uv sync
source .venv/bin/activate
```

### Permission errors

Some tools may require elevated permissions for port scanning:
```bash
# On Linux/Mac, may need sudo for naabu
sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip $(which naabu)
```

## Next Steps

1. **Test the PoC**: Run discovery against known safe targets
2. **Extend Active Discovery**: Implement HTTP probing stage (discovery/stages/active.py)
3. **Add Deep Discovery**: Implement web crawling stage (discovery/stages/deep.py)
4. **Implement Enrichment**: Add CVE mapping and risk scoring (discovery/stages/enrichment.py)
5. **Enhance Output**: Generate pentest recommendations

## Development

### Running Tests (when implemented)
```bash
uv run pytest tests/ -v
```

### Code Formatting
```bash
uv run black discovery/ tests/
```

### Type Checking
```bash
uv run mypy discovery/
```

## Support

For issues or questions:
- Review logs with `--verbose` flag
- Check tool installation with `--check-tools`
- Examine example output in `examples/example_output.json`
