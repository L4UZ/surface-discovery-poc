# Docker Troubleshooting Patterns - Surface Discovery

## Pattern: Binary Compatibility Across Build Stages

### Symptom
- Binary exists (`which tool` finds it)
- Execution fails with "not found" error
- Error occurs after COPY from build stage to runtime stage

### Diagnosis
```bash
# Check dynamic library dependencies
docker run --rm --entrypoint /bin/sh image -c 'ldd /path/to/binary'

# Look for "not found" in ldd output
# Example: libc.musl-aarch64.so.1 => not found
```

### Root Cause
Build stage and runtime stage use different libc implementations:
- Alpine uses musl libc
- Debian/Ubuntu use glibc
- Binaries dynamically linked to musl cannot run on glibc (and vice versa)

### Solution Options

#### Option 1: Match Base Images (RECOMMENDED)
```dockerfile
# Both stages use same OS family
FROM golang:1.24-bookworm AS builder    # Debian
FROM python:3.11-slim                   # Debian (bookworm-based)
```

#### Option 2: Static Binaries (LIMITED)
```dockerfile
# Build static binaries
ENV CGO_ENABLED=0
RUN go install -v tool@latest

# Only works if tool doesn't require CGO (e.g., no libpcap)
```

#### Option 3: Install Runtime Dependencies
```dockerfile
# Install musl in Debian runtime (not recommended)
RUN apt-get install -y musl
```

### Prevention
1. Document base image decisions in Dockerfile comments
2. Test binary execution in runtime stage during build
3. Use `ldd` to verify dynamic dependencies
4. Prefer matching OS families for multi-stage builds

## Pattern: Python Import Errors at Runtime

### Symptom
- Docker build succeeds
- Runtime fails with "ImportError: cannot import name 'X'"
- Import works in development but fails in container

### Diagnosis
```bash
# Test imports during build
RUN python -c "from discovery.models import DiscoveryStage, WHOISData"

# Check __all__ exports
docker run --rm image python -c "import discovery.models; print(discovery.models.__all__)"
```

### Root Cause
- Class defined in module but not exported in `__all__`
- Relative imports work but explicit imports fail
- Common with refactored code or new classes

### Solution
```python
# discovery/models/__init__.py

# Import all classes
from .domain import Subdomain, DNSRecords, DomainInfo, WHOISData
from .discovery import DiscoveryResult, DiscoveryMetadata, DiscoveryStage

# Export all classes
__all__ = [
    'Subdomain', 'DNSRecords', 'DomainInfo', 'WHOISData',
    'DiscoveryResult', 'DiscoveryMetadata', 'DiscoveryStage'
]
```

### Prevention
1. Test imports in Dockerfile: `RUN python -c "from module import Class"`
2. Use automated import validation in CI
3. Keep `__all__` synchronized with actual exports
4. Run container smoke tests before pushing

## Pattern: Go Module Download Timeouts

### Symptom
- Build fails during `go install` with network errors
- Error: "read tcp ... connection reset by peer"
- Intermittent failures during module download

### Diagnosis
```bash
# Check which modules are failing
docker build . 2>&1 | grep "connection reset"

# Identify large or problematic modules
```

### Root Cause
- Large Go module downloads timeout
- Network instability during build
- Single RUN command fails entire layer

### Solution
```dockerfile
# Separate RUN commands for better caching and retry
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
RUN go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest

# Each command becomes separate layer
# Failed download only requires rebuilding one layer
# Docker layer cache reuses successful downloads
```

### Prevention
1. Separate large downloads into individual RUN commands
2. Use Go module proxy with caching
3. Set appropriate build timeouts
4. Consider vendoring dependencies for critical builds

## Pattern: CLI Flag Validation

### Symptom
- `--check-tools` flag requires unrelated `--url` parameter
- Click validation fails before business logic runs
- Flag combinations not properly validated

### Diagnosis
```python
# Check Click option requirements
@click.option('--url', required=True)  # PROBLEM: Always required

# Test flag combinations
docker run --rm image --check-tools  # Fails
```

### Solution
```python
# Make flag optional in Click
@click.option('--url', required=False)

# Validate in business logic
def main(url, check_tools, ...):
    if check_tools:
        asyncio.run(check_dependencies())
        return
    
    if not url:  # Validate only when needed
        console.print("[red]Error: --url required[/red]")
        sys.exit(1)
```

### Prevention
1. Make flags optional at framework level
2. Implement validation in business logic
3. Test all flag combinations
4. Document flag dependencies in help text

## General Docker Build Best Practices

### Layer Caching Optimization
```dockerfile
# Copy dependencies first (changes less frequently)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code last (changes more frequently)
COPY discovery/ ./discovery/
COPY cli.py .
```

### Build Diagnostics
```bash
# Show full build log
docker build . 2>&1 | tee build.log

# Show only last N lines
docker build . 2>&1 | tail -50

# Check layer sizes
docker history image-name

# Inspect specific layer
docker inspect image-name
```

### Runtime Debugging
```bash
# Override entrypoint for shell access
docker run --rm -it --entrypoint /bin/bash image-name

# Check PATH and environment
docker run --rm image-name env

# Test specific command
docker run --rm --entrypoint /bin/sh image-name -c 'command'

# Check file permissions
docker run --rm --entrypoint ls image-name -la /path
```
