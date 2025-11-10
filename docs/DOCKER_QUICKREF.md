# Docker Quick Reference

One-page reference for Surface Discovery Docker commands.

## Build & Setup

```bash
# Build image
docker build -t surface-discovery .

# Build with docker-compose
docker-compose build

# Check tools installation
docker run --rm surface-discovery --check-tools
```

## Basic Usage

```bash
# Simple scan
docker run --rm -v $(pwd)/results:/output surface-discovery example.com

# Deep scan
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com --depth deep --verbose

# Custom output file
docker run --rm -v $(pwd)/results:/output \
  -e OUTPUT_FILE=/output/custom.json \
  surface-discovery example.com
```

## Docker Compose

```bash
# Run scan
docker-compose run --rm surface-discovery example.com

# Deep scan
docker-compose run --rm surface-discovery example.com --depth deep

# Multiple scans
for domain in example.com test.com; do
  docker-compose run --rm surface-discovery $domain
done
```

## Common Options

| Option | Example | Description |
|--------|---------|-------------|
| `--depth` | `--depth deep` | Discovery depth (shallow\|normal\|deep) |
| `--timeout` | `--timeout 1200` | Max execution time (seconds) |
| `--parallel` | `--parallel 20` | Max parallel tasks |
| `--verbose` | `--verbose` | Enable detailed logging |
| `--output` | `--output /output/scan.json` | Output file path |

## Volume Mounts

```bash
# Mount results directory
-v $(pwd)/results:/output

# Absolute path
-v /path/to/results:/output

# Windows (PowerShell)
-v ${PWD}/results:/output

# Windows (CMD)
-v %CD%/results:/output
```

## Environment Variables

```bash
# Custom output filename
-e OUTPUT_FILE=/output/scan_$(date +%Y%m%d).json

# Node.js settings
-e NODE_ENV=production
```

## Network Modes

```bash
# Host network (better performance)
docker run --rm --network host \
  -v $(pwd)/results:/output surface-discovery example.com

# Bridge network (default, more isolated)
docker run --rm --network bridge \
  -v $(pwd)/results:/output surface-discovery example.com
```

## Resource Limits

```bash
# CPU limit
docker run --rm --cpus="2.0" \
  -v $(pwd)/results:/output surface-discovery example.com

# Memory limit
docker run --rm -m 2g \
  -v $(pwd)/results:/output surface-discovery example.com

# Both
docker run --rm --cpus="2.0" -m 2g \
  -v $(pwd)/results:/output surface-discovery example.com
```

## Debugging

```bash
# Interactive shell
docker run --rm -it --entrypoint /bin/sh surface-discovery

# Run manual tools
docker run --rm -it surface-discovery /bin/sh
# Inside container:
$ subfinder -d example.com -silent
$ httpx -u https://example.com -json

# View logs
docker logs <container_id>

# Inspect image
docker inspect surface-discovery
```

## Automated Scanning

```bash
#!/bin/bash
# Scan multiple targets
for domain in $(cat targets.txt); do
  docker run --rm \
    -v $(pwd)/results:/output \
    -e OUTPUT_FILE="/output/scan_${domain}.json" \
    surface-discovery "$domain" --depth normal
done
```

## Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Complete cleanup
docker system prune -a --volumes
```

## CI/CD Example

```bash
# GitHub Actions / GitLab CI
docker build -t surface-discovery .
docker run --rm \
  -v $PWD/results:/output \
  surface-discovery ${TARGET_DOMAIN} --depth normal
```

## Troubleshooting

```bash
# Permission errors
chmod 777 results/

# Rebuild without cache
docker build --no-cache -t surface-discovery .

# Check container status
docker ps -a

# View build logs
docker build -t surface-discovery . 2>&1 | tee build.log
```

## Registry Operations

```bash
# Tag for registry
docker tag surface-discovery:latest myregistry.com/surface-discovery:latest

# Push to registry
docker push myregistry.com/surface-discovery:latest

# Pull from registry
docker pull myregistry.com/surface-discovery:latest
```

## Best Practices

✅ **DO**:
- Use volume mounts for persistent results
- Set resource limits for production
- Use host network for better scanning performance
- Clean up old containers and images regularly

❌ **DON'T**:
- Run without volume mounts (results will be lost)
- Use privileged mode unless absolutely necessary
- Ignore resource limits in production
- Hardcode credentials in environment variables

## Complete Example

```bash
#!/bin/bash
# Production-ready scan script

TARGET="$1"
OUTPUT_DIR="./results"
MAX_MEMORY="2g"
MAX_CPUS="2.0"
DEPTH="${DEPTH:-normal}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run scan with all best practices
docker run --rm \
  --network host \
  --cpus="$MAX_CPUS" \
  -m "$MAX_MEMORY" \
  -v "$(pwd)/$OUTPUT_DIR:/output" \
  -e OUTPUT_FILE="/output/scan_${TARGET//[^a-zA-Z0-9]/_}.json" \
  surface-discovery "$TARGET" \
  --depth "$DEPTH" \
  --timeout 900 \
  --parallel 15 \
  --verbose

echo "Scan complete: $OUTPUT_DIR/scan_${TARGET//[^a-zA-Z0-9]/_}.json"
```

Usage:
```bash
chmod +x scan.sh
./scan.sh example.com
DEPTH=deep ./scan.sh example.com
```
