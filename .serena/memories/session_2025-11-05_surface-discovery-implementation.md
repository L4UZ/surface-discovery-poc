# Surface Discovery - Docker Implementation Session

## Session Date: 2025-11-05

## Project Overview
Surface Discovery is a proof-of-concept web attack surface reconnaissance service that executes in-depth discovery using ProjectDiscovery tools (subfinder, httpx, nuclei, katana, dnsx, naabu).

## Session Accomplishments

### 1. Docker Build Issues Resolved
Successfully fixed multiple critical Docker build and runtime issues:

#### Go Version Compatibility (Dockerfile:3)
- **Error**: "requires go >= 1.24.0 (running go 1.21.13)"
- **Fix**: Updated base image from `golang:1.21-alpine` to `golang:1.24-bookworm`

#### Binary Compatibility - musl vs glibc (Dockerfile:3)
- **Error**: Tools compiled in Alpine (musl) failing to execute in Debian runtime (glibc)
- **Symptom**: "not found" errors when executing Go binaries, missing `libc.musl-aarch64.so.1`
- **Fix**: Changed from Alpine to Debian-based Go image (`golang:1.24-bookworm`) to match runtime environment
- **Root Cause**: Dynamic linking incompatibility between musl libc (Alpine) and glibc (Debian)

#### Python Import Errors (discovery/models/__init__.py)
- **Error 1**: "cannot import name 'DiscoveryStage' from 'discovery.models'"
- **Error 2**: "cannot import name 'WHOISData' from 'discovery.models'"
- **Fix**: Added both classes to `__all__` exports in models/__init__.py

#### CLI Flag Validation (cli.py:26, 85-88)
- **Error**: `--check-tools` flag required `--url` parameter
- **Fix**: Made `--url` optional and added validation to require it only for normal discovery operations

#### Network Dependencies (Dockerfile:13-18)
- **Error**: Timeout downloading Go module dependencies during build
- **Fix**: Separated `go install` commands into individual RUN statements for better layer caching and retry capability

### 2. Project Structure
```
surface-discovery/
├── discovery/
│   ├── config.py           # Configuration with depth presets
│   ├── core.py             # Main orchestration engine
│   ├── models/
│   │   ├── __init__.py     # Model exports (FIXED)
│   │   ├── domain.py       # Domain-related models
│   │   ├── service.py      # Service/technology models
│   │   ├── finding.py      # Security findings models
│   │   └── discovery.py    # Discovery metadata models
│   ├── stages/
│   │   └── passive.py      # Passive discovery (WORKING)
│   ├── tools/
│   │   ├── runner.py       # Async subprocess runner
│   │   └── parsers.py      # Tool output parsers
│   └── utils/
│       ├── logger.py       # Logging configuration
│       └── helpers.py      # Utility functions
├── cli.py                  # CLI interface (FIXED)
├── Dockerfile              # Multi-stage build (FIXED)
├── docker-compose.yml      # Orchestration config
├── docker-entrypoint.sh    # Smart entrypoint
├── requirements.txt        # Python dependencies
└── tests/                  # Test suite

Documentation:
├── README.md               # Main documentation
├── DOCKER.md               # Docker deployment guide
├── DOCKER_QUICKREF.md      # Quick reference
└── TROUBLESHOOTING.md      # 30+ common issues
```

### 3. Current Status

**✅ WORKING:**
- Docker multi-stage build successfully compiles and packages all tools
- All 6 ProjectDiscovery tools installed and verified (subfinder, httpx, nuclei, katana, dnsx, naabu)
- Passive discovery stage functional (subdomain enumeration + DNS resolution)
- CLI interface with rich output formatting
- JSON result export with comprehensive metadata
- Test execution: Successfully discovered 20 subdomains for example.com in 8.94 seconds

**⚠️ NOT YET IMPLEMENTED:**
- Active discovery stage (service enumeration, port scanning)
- Deep discovery stage (web crawling, endpoint discovery)
- Enrichment stage (technology detection, vulnerability scanning)

### 4. Technical Decisions

#### Multi-Stage Docker Build
- **Stage 1**: Debian-based Go builder (`golang:1.24-bookworm`) for ProjectDiscovery tools
- **Stage 2**: Python 3.11 slim runtime for application execution
- **Why**: Separates build dependencies from runtime, reduces final image size

#### Binary Compatibility Strategy
- **Decision**: Use matching Debian base for both build and runtime stages
- **Alternative Rejected**: Static Go binaries (CGO_ENABLED=0) - naabu requires libpcap
- **Reason**: Ensures binary compatibility while maintaining required dynamic linking

#### Async Architecture
- **Pattern**: asyncio for concurrent tool execution
- **Benefits**: Parallel subprocess execution, better resource utilization
- **Implementation**: ToolRunner class with async/await patterns

#### Data Models
- **Framework**: Pydantic v2 for type safety and validation
- **Structure**: Layered models (domain, service, finding, discovery metadata)
- **Export**: JSON serialization with datetime handling

### 5. Key Files Modified

#### Dockerfile (6 fixes applied)
```dockerfile
FROM golang:1.24-bookworm AS go-builder  # Changed from alpine
RUN apt-get install -y libpcap-dev       # Added for naabu
RUN go install [tool]                    # Separated for caching
```

#### discovery/models/__init__.py
```python
from .domain import Subdomain, DNSRecords, DomainInfo, WHOISData  # Added WHOISData
from .discovery import DiscoveryResult, DiscoveryMetadata, DiscoveryStage  # Added DiscoveryStage

__all__ = [
    'Subdomain', 'DNSRecords', 'DomainInfo', 'WHOISData',  # All exports
    'DiscoveryResult', 'DiscoveryMetadata', 'DiscoveryStage'
]
```

#### cli.py
```python
@click.option('--url', required=False)  # Changed from required=True

if check_tools:
    asyncio.run(check_dependencies())
    return

if not url:  # Added validation
    console.print("[bold red]Error:[/bold red] --url is required")
    sys.exit(1)
```

### 6. Testing Results

#### Tools Check
```bash
$ docker run --rm surface-discovery --check-tools
✓ All required tools are installed!
- dnsx, httpx, katana, naabu, nuclei, subfinder
```

#### Discovery Execution
```bash
$ docker run --rm -v $(pwd)/results:/output surface-discovery example.com --depth shallow
Target: example.com
Duration: 8.94 seconds
Total Subdomains: 20
Completeness: 30.0%
```

#### Output Validation
- JSON file created: `discovery_results.json` (8.6KB)
- Structured metadata with timestamps
- Discovery timeline with stage progression
- Statistics and findings data structures

### 7. Next Steps (Not Requested)

The following stages were planned but not yet requested by the user:
1. Implement active discovery stage (httpx, naabu)
2. Implement deep discovery stage (katana, endpoint enumeration)
3. Implement enrichment stage (nuclei, technology detection)
4. Add comprehensive test suite
5. Add CI/CD pipeline integration

### 8. Lessons Learned

#### Docker Multi-Stage Builds
- **Lesson**: Base image libc compatibility is critical for cross-stage binaries
- **Pattern**: Match build and runtime base OS family (Debian-to-Debian, Alpine-to-Alpine)
- **Detection**: "not found" errors despite binary existing = dynamic linking issue

#### Go Binary Compatibility
- **Lesson**: Alpine (musl) and Debian (glibc) have different libc implementations
- **Solution 1**: Use matching base images (recommended)
- **Solution 2**: Build static binaries (CGO_ENABLED=0) - not possible with libpcap dependencies
- **Diagnosis**: Use `ldd` to check dynamic library dependencies

#### Python Import Debugging
- **Lesson**: Always verify `__all__` exports match actual imports
- **Pattern**: Import errors at runtime despite successful image build
- **Prevention**: Test imports during Docker build or in CI

#### Network Resilience
- **Lesson**: Large Go module downloads can timeout during Docker build
- **Solution**: Separate RUN commands for better layer caching and retry capability
- **Benefit**: Failed downloads only require rebuilding specific layers

### 9. Command Reference

```bash
# Build image
docker build -t surface-discovery .

# Check tools
docker run --rm surface-discovery --check-tools

# Run discovery (shallow)
docker run --rm -v $(pwd)/results:/output surface-discovery example.com --depth shallow

# Run discovery (normal)
docker run --rm -v $(pwd)/results:/output surface-discovery example.com --depth normal

# Run with custom timeout
docker run --rm -v $(pwd)/results:/output surface-discovery example.com --timeout 1800

# Interactive shell for debugging
docker run --rm -it --entrypoint /bin/bash surface-discovery

# Check tool versions
docker run --rm --entrypoint /bin/sh surface-discovery -c 'subfinder -version'
```

### 10. Architecture Patterns

#### Discovery Pipeline
```python
discover(target_url) →
  _run_passive_discovery() →     # IMPLEMENTED
  _run_active_discovery() →      # PLACEHOLDER
  _run_deep_discovery() →        # PLACEHOLDER
  _run_enrichment() →            # PLACEHOLDER
  _finalize()
```

#### Async Tool Execution
```python
ToolRunner.run(command, timeout) →
  asyncio.create_subprocess_exec() →
  asyncio.wait_for(process.communicate(), timeout) →
  return (stdout, stderr, returncode)
```

#### Result Aggregation
```python
DiscoveryResult:
  - metadata: DiscoveryMetadata
  - subdomains: List[Subdomain]
  - services: List[Service]
  - findings: List[Finding]
  - statistics: Statistics
  - discovery_timeline: List[TimelineEvent]
```
