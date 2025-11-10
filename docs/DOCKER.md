# Docker Deployment Guide

Complete guide for running Surface Discovery in Docker with all dependencies bundled.

## Quick Start

### 1. Build the Image

```bash
docker build -t surface-discovery .
```

This builds a multi-stage image that includes:
- All Go-based security tools (subfinder, httpx, naabu, katana, dnsx)
- Node.js 20+ runtime and dependencies
- Configured non-root user
- Network capabilities for port scanning

Build time: ~5-10 minutes (depending on network speed)

### 2. Run Discovery

#### Simple Run (URL as argument)
```bash
# Basic discovery
docker run --rm -v $(pwd)/results:/output surface-discovery example.com

# Deep discovery with verbose output
docker run --rm -v $(pwd)/results:/output surface-discovery example.com --depth deep --verbose

# Custom output filename
docker run --rm \
  -v $(pwd)/results:/output \
  -e OUTPUT_FILE=/output/custom_scan.json \
  surface-discovery example.com
```

#### Using Full CLI Options
```bash
docker run --rm -v $(pwd)/results:/output surface-discovery \
  --url example.com \
  --output /output/scan_results.json \
  --depth normal \
  --timeout 900 \
  --parallel 15 \
  --verbose
```

## Docker Compose

### Build and Run with Docker Compose

```bash
# Build the image
docker-compose build

# Run discovery
docker-compose run --rm surface-discovery example.com --depth deep

# Check tools
docker-compose run --rm surface-discovery --check-tools

# View help
docker-compose run --rm surface-discovery --help
```

### Persistent Results Directory

Results are automatically saved to `./results/` directory:

```bash
# Create results directory
mkdir -p results

# Run discovery
docker-compose run --rm surface-discovery example.com

# View results
cat results/discovery_results.json
```

## Usage Examples

### Basic Reconnaissance
```bash
# Simple subdomain discovery
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com
```

### Comprehensive Discovery
```bash
# Deep discovery with all features
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com \
  --depth deep \
  --timeout 1200 \
  --verbose
```

### Multiple Targets
```bash
# Scan multiple targets
for domain in example.com test.com demo.org; do
  docker run --rm -v $(pwd)/results:/output \
    surface-discovery $domain --depth shallow
done
```

### Custom Configuration
```bash
# Override default settings
docker run --rm \
  -v $(pwd)/results:/output \
  -e OUTPUT_FILE=/output/custom_name.json \
  surface-discovery example.com \
  --parallel 20 \
  --timeout 1800
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTPUT_FILE` | `/output/discovery_results.json` | Default output file path |
| `NODE_ENV` | `production` | Node.js environment mode |

Example:
```bash
docker run --rm \
  -v $(pwd)/results:/output \
  -e OUTPUT_FILE=/output/scan_$(date +%Y%m%d).json \
  surface-discovery example.com
```

## Volume Mounts

### Output Directory (Required)
```bash
# Mount current directory's results folder
-v $(pwd)/results:/output

# Mount absolute path
-v /path/to/results:/output
```

### Configuration Files (Optional)
```bash
# Mount custom config
-v $(pwd)/custom_config.ts:/app/src/config.ts
```

## Network Configuration

### Host Network Mode (Recommended for Scanning)
```bash
# Use host network for better performance
docker run --rm --network host \
  -v $(pwd)/results:/output \
  surface-discovery example.com
```

### Bridge Network Mode (Isolated)
```bash
# Use bridge network (default, more secure but slower)
docker run --rm --network bridge \
  -v $(pwd)/results:/output \
  surface-discovery example.com
```

## Security Considerations

### Capabilities

The container requires these capabilities for port scanning:
- `CAP_NET_RAW`: Raw socket access
- `CAP_NET_ADMIN`: Network administration
- `CAP_NET_BIND_SERVICE`: Bind to privileged ports

These are set in the Dockerfile via `setcap` for the `naabu` binary.

### Running as Non-Root

The container runs as user `discovery` (UID 1000) by default for security.

### Privileged Mode (Not Recommended)

If you encounter permission issues, you can run in privileged mode (use with caution):

```bash
# NOT RECOMMENDED - only if required
docker run --rm --privileged \
  -v $(pwd)/results:/output \
  surface-discovery example.com
```

## Troubleshooting

### Permission Errors on Output
```bash
# Ensure results directory is writable
chmod 777 results/

# Or run with matching user ID
docker run --rm --user $(id -u):$(id -g) \
  -v $(pwd)/results:/output \
  surface-discovery example.com
```

### Tool Not Found Errors
```bash
# Verify tools are installed
docker run --rm surface-discovery --check-tools

# Rebuild image if tools are missing
docker build --no-cache -t surface-discovery .
```

### Network Issues
```bash
# Use host network mode
docker run --rm --network host \
  -v $(pwd)/results:/output \
  surface-discovery example.com

# Test DNS resolution
docker run --rm surface-discovery nslookup example.com
```

### Memory Issues
```bash
# Increase memory limit
docker run --rm -m 4g \
  -v $(pwd)/results:/output \
  surface-discovery example.com --depth deep
```

## Advanced Usage

### Interactive Shell Access
```bash
# Enter container for debugging
docker run --rm -it --entrypoint /bin/sh surface-discovery

# Run manual commands inside container
docker run --rm -it surface-discovery /bin/sh
# Inside container:
$ subfinder -d example.com -silent
$ httpx -l subdomains.txt -json
```

### Custom Entrypoint
```bash
# Override entrypoint to run custom commands
docker run --rm --entrypoint node surface-discovery \
  -e "import('./dist/core.js').then(m => { console.log('Custom script'); })"
```

### Build with Custom Tag
```bash
# Build with version tag
docker build -t surface-discovery:v0.1.0 .

# Tag for registry
docker tag surface-discovery:latest myregistry/surface-discovery:latest
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Run Surface Discovery

on:
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t surface-discovery .

      - name: Run discovery
        run: |
          docker run --rm \
            -v ${{ github.workspace }}/results:/output \
            surface-discovery ${{ secrets.TARGET_DOMAIN }} \
            --depth normal

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: discovery-results
          path: results/
```

### GitLab CI Example
```yaml
scan:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t surface-discovery .
    - mkdir -p results
    - docker run --rm -v $(pwd)/results:/output surface-discovery $TARGET_DOMAIN
  artifacts:
    paths:
      - results/
```

## Performance Optimization

### Build Cache
```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker build -t surface-discovery .
```

### Layer Caching
The Dockerfile is optimized for layer caching:
1. Go tools (changes rarely)
2. Node.js dependencies (changes occasionally)
3. Application code (changes frequently)

### Multi-Architecture Build
```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 \
  -t surface-discovery:latest .
```

## Image Size Optimization

Current image size: ~800MB-1GB (includes all tools)

To reduce size:
```bash
# Remove unnecessary tools from Dockerfile
# Use alpine-based images where possible
# Clean up apt cache and temporary files
```

## Docker Registry

### Push to Registry
```bash
# Tag for registry
docker tag surface-discovery:latest myregistry.com/surface-discovery:latest

# Push to registry
docker push myregistry.com/surface-discovery:latest

# Pull and run
docker pull myregistry.com/surface-discovery:latest
docker run --rm -v $(pwd)/results:/output \
  myregistry.com/surface-discovery:latest example.com
```

## Health Checks

Add to `docker-compose.yml`:
```yaml
healthcheck:
  test: ["CMD", "node", "dist/cli.js", "--check-tools"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Resource Limits

### CPU Limits
```bash
docker run --rm --cpus="2.0" \
  -v $(pwd)/results:/output \
  surface-discovery example.com
```

### Memory Limits
```bash
docker run --rm -m 2g --memory-swap 2g \
  -v $(pwd)/results:/output \
  surface-discovery example.com
```

## Cleanup

### Remove Container and Volumes
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove volumes
docker volume prune
```

### Complete Cleanup
```bash
# Remove everything related to surface-discovery
docker ps -a | grep surface-discovery | awk '{print $1}' | xargs docker rm
docker images | grep surface-discovery | awk '{print $3}' | xargs docker rmi
```

## Automated Scanning Script

```bash
#!/bin/bash
# automated_scan.sh

TARGETS_FILE="targets.txt"
OUTPUT_DIR="./results"
DEPTH="${DEPTH:-normal}"

mkdir -p "$OUTPUT_DIR"

while IFS= read -r target; do
  echo "Scanning $target..."

  docker run --rm \
    -v "$(pwd)/$OUTPUT_DIR:/output" \
    -e OUTPUT_FILE="/output/scan_${target//[^a-zA-Z0-9]/_}.json" \
    surface-discovery "$target" \
    --depth "$DEPTH" \
    --verbose

  echo "Completed: $target"
done < "$TARGETS_FILE"

echo "All scans completed. Results in $OUTPUT_DIR/"
```

Usage:
```bash
chmod +x automated_scan.sh
./automated_scan.sh
```

## Support

For issues:
1. Check logs: `docker logs <container_id>`
2. Verify tools: `docker run --rm surface-discovery --check-tools`
3. Rebuild image: `docker build --no-cache -t surface-discovery .`
4. Test locally: `docker run --rm -it surface-discovery /bin/sh`
