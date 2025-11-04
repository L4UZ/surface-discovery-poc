# Quick Start Guide

## Installation

### 1. Install External Tools

```bash
# Install Go-based security tools
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
```

Ensure `~/go/bin` is in your PATH:
```bash
export PATH=$PATH:~/go/bin
```

### 2. Setup Python Environment

```bash
cd surface-discovery
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python cli.py --check-tools
```

You should see all tools marked as "✓ Installed".

## Basic Usage

### Simple Discovery

```bash
python cli.py --url example.com
```

This will:
- Discover subdomains
- Collect DNS records
- Save results to `discovery_example_com.json`

### Custom Output File

```bash
python cli.py --url example.com --output my_results.json
```

### Deep Discovery

```bash
python cli.py --url example.com --depth deep --verbose
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
python cli.py --url example.com --depth shallow
```

### Vulnerable Test Target
```bash
# Test with intentionally vulnerable site (requires permission!)
python cli.py --url testphp.vulnweb.com --depth normal --verbose
```

### Custom Configuration
```bash
# Override specific settings
python cli.py \
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

Activate virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
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
pytest tests/ -v
```

### Code Formatting
```bash
black discovery/ tests/
```

### Type Checking
```bash
mypy discovery/
```

## Support

For issues or questions:
- Review logs with `--verbose` flag
- Check tool installation with `--check-tools`
- Examine example output in `examples/example_output.json`
