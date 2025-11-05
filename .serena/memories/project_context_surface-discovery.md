# Surface Discovery - Project Context

## Project Type
Production-ready web attack surface reconnaissance service

## Technology Stack
- **Language**: Python 3.11
- **Security Tools**: ProjectDiscovery suite (subfinder, httpx, nuclei, katana, dnsx, naabu)
- **Async Framework**: asyncio for concurrent execution
- **Data Validation**: Pydantic v2
- **CLI Framework**: Click
- **Output**: Rich terminal UI, JSON export
- **Deployment**: Docker multi-stage build

## Core Architecture

### Discovery Pipeline (6 stages) - ALL COMPLETE ✅
1. **Passive Discovery** ✅ - Subdomain enumeration, DNS resolution
2. **Active Discovery** ✅ - HTTP probing, technology detection
3. **Deep Discovery** ✅ - Web crawling, endpoint discovery
4. **Enrichment** ✅ - Infrastructure intelligence (cloud/CDN providers, ASN)
5. **Vulnerability Scanning** ✅ - Nuclei template-based security scanning (toggleable)
6. **Authenticated Discovery** ✅ - Session-based authenticated crawling

### Key Components
- **discovery/core.py**: Main orchestration engine with async pipeline
- **discovery/tools/runner.py**: Async subprocess execution wrapper for security tools
- **discovery/stages/**: Complete stage implementations (passive, active, deep, enrichment, vulnerability, authenticated)
- **discovery/models/**: Pydantic data models for all result types
- **discovery/config.py**: Depth-based configuration presets with stage toggles
- **cli.py**: Rich CLI interface with Click framework

## Configuration
- **Depth Presets**: shallow (quick), normal (standard), deep (comprehensive)
- **Parallel Execution**: Configurable concurrent task limit (default: 10)
- **Timeouts**: Per-tool timeouts (subfinder: 180s, httpx: 180s, nuclei: 180s, etc.)
- **Stage Toggles**: --skip-vuln-scan flag to skip vulnerability scanning
- **Output**: Configurable JSON output path with auto-generated filenames

## Docker Architecture
- **Build Stage**: golang:1.24-bookworm (ProjectDiscovery tools installation)
- **Runtime Stage**: python:3.11-slim (application execution)
- **Security**: Non-root user (discovery:1000)
- **Capabilities**: CAP_NET_RAW, CAP_NET_ADMIN for naabu port scanning
- **Volumes**: /output for results persistence

## CLI Flags
- `--url`: Target URL or domain (required)
- `--output`: Output file path (auto-generated if not provided)
- `--depth`: Discovery depth (shallow|normal|deep)
- `--timeout`: Max execution time in seconds
- `--parallel`: Max parallel tasks
- `--verbose`: Enable verbose logging
- `--check-tools`: Verify tool installation
- `--auth-mode`: Enable authenticated discovery
- `--auth-config`: YAML authentication configuration file
- `--skip-vuln-scan`: Skip vulnerability scanning stage (NEW)

## Recent Bug Fixes

### Nuclei JSON Parsing Error (2025-11-05) ✅
**Issue**: `Failed to parse nuclei JSON: Expecting value: line 1 column 1 (char 0)`

**Root Causes**:
1. Wrong nuclei flag: `-json` instead of `-jsonl` (runner.py:268)
2. Missing tags parameter in run_nuclei() function
3. No empty output handling before JSON parsing

**Fixes**:
- Changed to `-jsonl` flag in discovery/tools/runner.py:270
- Added tags parameter and handling (lines 254, 276-277)
- Added empty output check in vulnerability.py (lines 182-184)
- Enhanced error handling with debug logging (lines 187-201)

### Vulnerability Scanning Toggle (2025-11-05) ✅
**Feature**: Optional vulnerability scanning via --skip-vuln-scan flag

**Implementation**:
- cli.py: Added --skip-vuln-scan flag (lines 72-76, 87, 127-128)
- config.py: Added skip_vuln_scan field (lines 34-35)
- core.py: Added conditional execution logic (lines 86-94)
- Timeline event: Records skip action for audit trail

**Benefits**: 30-50% faster execution when vulnerabilities aren't needed

## Known Issues Resolved
1. ✅ Go version compatibility (requires 1.24+)
2. ✅ Binary compatibility (musl vs glibc)
3. ✅ Python import exports (DiscoveryStage, WHOISData)
4. ✅ CLI flag validation (--check-tools without --url)
5. ✅ Nuclei JSON parsing error (format mismatch)
6. ✅ Missing template tags in nuclei execution

## Development Status
- **Core Implementation**: ✅ Complete (all 6 stages working)
- **Docker Packaging**: ✅ Complete and tested
- **Documentation**: ✅ Comprehensive (README, DOCKER.md, TROUBLESHOOTING.md)
- **Testing**: ✅ Manual testing complete, automated tests pending
- **Feature Toggles**: ✅ Vulnerability scan toggle implemented

## Output Format
Comprehensive JSON including:
- Metadata (scan_id, duration, completeness)
- Domains (subdomains with DNS records, WHOIS data)
- Services (HTTP/HTTPS probing results with technologies)
- Endpoints (crawled URLs with parameters)
- Technologies (detected tech stack)
- Infrastructure (cloud providers, CDN, ASN mappings)
- Findings (vulnerability scan results by severity)
- Statistics (aggregated metrics)
- Timeline (discovery event log)

## Performance Characteristics
- **Shallow depth**: ~30-60s (20 subdomains limit, depth 2 crawling)
- **Normal depth**: ~3-10min (unlimited subdomains, depth 3 crawling)
- **Deep depth**: ~10-15min (unlimited subdomains, depth 5 crawling)
- **With --skip-vuln-scan**: 30-50% faster execution

## Authentication Support
- **Config Format**: YAML with multiple authentication methods
- **Methods**: Session cookies, JWT tokens, OAuth2 headers, custom headers
- **Flow**: Normal discovery → Authenticated crawling → Combined results
- **Output**: Authenticated endpoints marked and counted separately
