# Troubleshooting Guide

Common issues and solutions for Surface Discovery Docker deployment.

## Quick Diagnostics

### Validation Scripts

Run these scripts to diagnose issues:

```bash
# Quick validation (no build required)
./validate-docker.sh

# Full test suite (includes build and execution)
./test-docker-improved.sh
```

---

## Common Issues

### 1. Docker Build Failures

#### Issue: "Cannot connect to Docker daemon"
```
ERROR: Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solutions:**
```bash
# Check if Docker is running
docker info

# Start Docker Desktop (macOS/Windows)
# Or start Docker daemon (Linux)
sudo systemctl start docker

# Verify daemon is running
docker ps
```

#### Issue: "Go tools installation fails"
```
ERROR: go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```

**Solutions:**
1. Check internet connection
2. Rebuild without cache:
```bash
docker build --no-cache -t surface-discovery .
```
3. Use alternative base image in Dockerfile:
```dockerfile
FROM golang:1.22-alpine AS go-builder  # Try newer version
```

#### Issue: "Build timeout"
```
ERROR: Build exceeded timeout
```

**Solutions:**
```bash
# Increase build timeout
docker build --timeout=900 -t surface-discovery .

# Or use BuildKit with better caching
DOCKER_BUILDKIT=1 docker build -t surface-discovery .
```

---

### 2. Runtime Errors

#### Issue: "Permission denied" on output directory
```
ERROR: Permission denied: /output/discovery_results.json
```

**Solutions:**
```bash
# Ensure output directory is writable
mkdir -p results
chmod 777 results

# Or run with matching user ID (Linux)
docker run --rm --user $(id -u):$(id -g) \
  -v $(pwd)/results:/output surface-discovery example.com

# Or run as root (not recommended)
docker run --rm \
  -v $(pwd)/results:/output \
  --user root \
  surface-discovery example.com
```

#### Issue: "Tool not found" errors
```
ERROR: Tool not found: subfinder
```

**Solutions:**
1. Verify tools are in the image:
```bash
docker run --rm surface-discovery --check-tools
```

2. Check PATH in container:
```bash
docker run --rm surface-discovery /bin/sh -c 'echo $PATH'
docker run --rm surface-discovery /bin/sh -c 'which subfinder'
```

3. Rebuild image from scratch:
```bash
docker rmi surface-discovery
docker build -t surface-discovery .
```

#### Issue: "Network timeout" during discovery
```
ERROR: Timeout waiting for subfinder
```

**Solutions:**
```bash
# Use host network mode
docker run --rm --network host \
  -v $(pwd)/results:/output surface-discovery example.com

# Increase timeout
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com --timeout 1800
```

---

### 3. Entrypoint Issues

#### Issue: "Entrypoint script not executable"
```
ERROR: /entrypoint.sh: Permission denied
```

**Solutions:**
```bash
# Fix permissions before building
chmod +x docker-entrypoint.sh

# Or fix in Dockerfile (already included):
RUN chmod +x /entrypoint.sh
```

#### Issue: "Arguments not passed correctly"
```
ERROR: URL not recognized
```

**Solutions:**
```bash
# Use full CLI syntax
docker run --rm -v $(pwd)/results:/output \
  surface-discovery --url example.com --output /output/results.json

# Instead of short syntax
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com  # May fail depending on entrypoint logic
```

---

### 4. Volume Mount Issues

#### Issue: "Results not saved" (empty results directory)
```
ls results/  # Empty!
```

**Solutions:**
```bash
# Use absolute paths
docker run --rm \
  -v "$(pwd)/results:/output" \  # Note the quotes
  surface-discovery example.com

# On Windows (PowerShell)
docker run --rm `
  -v "${PWD}/results:/output" `
  surface-discovery example.com

# On Windows (CMD)
docker run --rm ^
  -v "%CD%/results:/output" ^
  surface-discovery example.com

# Verify mount works
docker run --rm -v $(pwd)/results:/output \
  surface-discovery /bin/sh -c "ls -la /output && touch /output/test.txt"
ls results/test.txt  # Should exist
```

---

### 5. Docker Compose Issues

#### Issue: "docker-compose: command not found"
```
ERROR: docker-compose: command not found
```

**Solutions:**
```bash
# Use newer docker compose (no hyphen)
docker compose up

# Or install docker-compose
pip install docker-compose

# Or use docker run directly (compose not required)
docker run --rm -v $(pwd)/results:/output surface-discovery example.com
```

#### Issue: "Compose file version not supported"
```
ERROR: Version in "./docker-compose.yml" is unsupported
```

**Solutions:**
Edit `docker-compose.yml`:
```yaml
# Change version to match your Docker Compose version
version: '3.8'  # Try '3.3' or remove version line entirely
```

---

### 6. Resource Issues

#### Issue: "Out of memory" during build
```
ERROR: Killed (Out of memory)
```

**Solutions:**
```bash
# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → 4GB+

# Clean up Docker resources
docker system prune -a --volumes

# Build with fewer parallel jobs
docker build --cpus=1 -m 2g -t surface-discovery .
```

#### Issue: "Disk space" errors
```
ERROR: No space left on device
```

**Solutions:**
```bash
# Clean up Docker
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove old containers
docker container prune

# Check disk space
df -h
```

---

### 7. Network Issues

#### Issue: "DNS resolution fails"
```
ERROR: Could not resolve host: github.com
```

**Solutions:**
```bash
# Use alternative DNS in build
docker build --build-arg HTTP_PROXY= --build-arg HTTPS_PROXY= \
  --dns 8.8.8.8 -t surface-discovery .

# Or configure Docker daemon DNS
# Edit /etc/docker/daemon.json:
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
```

#### Issue: "Port scanning fails"
```
ERROR: naabu: permission denied
```

**Solutions:**
```bash
# Use host network mode
docker run --rm --network host \
  -v $(pwd)/results:/output surface-discovery example.com

# Or add capabilities (already in Dockerfile)
docker run --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/results:/output surface-discovery example.com

# Or run as root (not recommended)
docker run --rm --user root \
  -v $(pwd)/results:/output surface-discovery example.com
```

---

## Debugging Commands

### Inspect the Image

```bash
# View image details
docker inspect surface-discovery

# View image layers
docker history surface-discovery

# Check image size
docker images surface-discovery

# View build log
docker build -t surface-discovery . 2>&1 | tee build.log
```

### Interactive Debugging

```bash
# Enter container shell
docker run --rm -it --entrypoint /bin/sh surface-discovery

# Inside container, test tools:
$ subfinder -h
$ httpx -h
$ python --version
$ ls -la /app
$ whoami
$ env
```

### Test Individual Components

```bash
# Test entrypoint
docker run --rm surface-discovery --help

# Test tool check
docker run --rm surface-discovery --check-tools

# Test with verbose logging
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com --verbose

# Run custom command
docker run --rm --entrypoint /bin/sh surface-discovery \
  -c "subfinder -d example.com -silent"
```

### Check Logs

```bash
# Run in background
docker run -d --name discovery-test \
  -v $(pwd)/results:/output surface-discovery example.com

# View logs
docker logs discovery-test

# Follow logs
docker logs -f discovery-test

# Stop container
docker stop discovery-test
docker rm discovery-test
```

---

## Platform-Specific Issues

### macOS

#### Issue: "Slow file I/O"
```
WARNING: Build or execution is very slow
```

**Solutions:**
```bash
# Use delegated mount (macOS)
docker run --rm \
  -v $(pwd)/results:/output:delegated \
  surface-discovery example.com

# Or use named volume (faster)
docker volume create discovery-results
docker run --rm \
  -v discovery-results:/output \
  surface-discovery example.com

# Extract results
docker run --rm \
  -v discovery-results:/output \
  -v $(pwd):/host \
  alpine sh -c "cp /output/* /host/"
```

### Windows

#### Issue: "Line ending issues"
```
ERROR: /entrypoint.sh: not found (CRLF line endings)
```

**Solutions:**
```bash
# Convert line endings (Git Bash)
dos2unix docker-entrypoint.sh

# Or configure Git
git config core.autocrlf input
git rm --cached -r .
git reset --hard
```

#### Issue: "Path translation"
```
ERROR: Invalid mount path
```

**Solutions:**
```powershell
# PowerShell
docker run --rm `
  -v "${PWD}/results:/output" `
  surface-discovery example.com

# CMD
docker run --rm ^
  -v "%CD%\results:/output" ^
  surface-discovery example.com

# Git Bash (enable path translation)
export MSYS_NO_PATHCONV=1
docker run --rm -v $(pwd)/results:/output surface-discovery example.com
```

### Linux

#### Issue: "Permission issues with volume mounts"
```
ERROR: Cannot write to /output
```

**Solutions:**
```bash
# Run with matching UID/GID
docker run --rm --user $(id -u):$(id -g) \
  -v $(pwd)/results:/output surface-discovery example.com

# Or fix directory permissions
chmod 777 results/

# Or run as root (not recommended)
docker run --rm --user root \
  -v $(pwd)/results:/output surface-discovery example.com
```

---

## Performance Optimization

### Faster Builds

```bash
# Use BuildKit
export DOCKER_BUILDKIT=1
docker build -t surface-discovery .

# Use layer caching effectively
# (already optimized in Dockerfile)

# Build in parallel
docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t surface-discovery .
```

### Faster Execution

```bash
# Use host network
docker run --rm --network host \
  -v $(pwd)/results:/output surface-discovery example.com

# Increase parallel tasks
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com --parallel 20

# Use shallow discovery for testing
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com --depth shallow
```

---

## Getting Help

### Collect Diagnostic Information

```bash
# Save all diagnostic info
cat > diagnostics.txt <<EOF
Docker version: $(docker --version)
Docker info:
$(docker info 2>&1)

Image info:
$(docker images surface-discovery 2>&1)

Tool check:
$(docker run --rm surface-discovery --check-tools 2>&1)

System info:
$(uname -a)
$(df -h .)
EOF

# Share diagnostics.txt when reporting issues
```

### Minimal Reproduction

```bash
# Create minimal test case
docker run --rm surface-discovery --help

# Test with simple target
docker run --rm -v $(pwd)/results:/output \
  surface-discovery example.com --depth shallow --verbose

# Share exact error messages and logs
```

### Community Support

- **GitHub Issues**: https://github.com/your-repo/surface-discovery/issues
- **Documentation**: Check DOCKER.md and README.md
- **Docker Docs**: https://docs.docker.com
- **ProjectDiscovery**: https://projectdiscovery.io

---

## Preventive Measures

### Before Building

```bash
# Always validate first
./validate-docker.sh

# Ensure clean state
docker system prune -f

# Check disk space
df -h .
```

### During Development

```bash
# Test incrementally
./test-docker-improved.sh

# Use verbose mode
docker build -t surface-discovery . --progress=plain

# Save build logs
docker build -t surface-discovery . 2>&1 | tee build.log
```

### After Changes

```bash
# Rebuild without cache
docker build --no-cache -t surface-discovery .

# Run full test suite
./test-docker-improved.sh

# Verify in clean environment
docker rmi surface-discovery
docker build -t surface-discovery .
docker run --rm surface-discovery --check-tools
```
