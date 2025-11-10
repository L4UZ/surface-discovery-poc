# Authenticated Scanning Guide

> ⚠️ **NOTE**: This document is pending update for the Node.js implementation. Examples currently show Python CLI commands and YAML configuration. The Node.js version uses:
> - CLI: `node dist/cli.js --auth-config config.json` (not `python cli.py --auth-config config.yaml`)
> - Config format: JSON (not YAML)
> - Full update in progress.

This guide explains how to configure and run authenticated discovery scans to access protected areas of your target application.

## Table of Contents

- [Overview](#overview)
- [Authentication Methods](#authentication-methods)
- [Configuration File Format](#configuration-file-format)
- [Docker Usage](#docker-usage)
- [Local Usage](#local-usage)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Overview

Authenticated discovery mode allows Surface Discovery to crawl protected areas of web applications by providing authentication credentials. This significantly expands the attack surface analysis by including:

- Private API endpoints
- User dashboards and authenticated pages
- Admin panels and privileged functionality
- Protected forms and interactive elements
- Session-based workflows

### What Gets Scanned with Authentication?

When `--auth-mode` is enabled, the tool performs:

1. **Stage 3: Deep Discovery (Authenticated)** - Crawls authenticated endpoints using provided credentials
2. **Stage 6: Authenticated Discovery** - Additional authenticated-only surface mapping
3. All other stages run normally with authentication context preserved

## Authentication Methods

Surface Discovery supports multiple authentication methods that can be combined:

### 1. Bearer Token / JWT Authentication

Common for modern APIs and SPAs:

```yaml
authentication:
  - url: "https://api.example.com"
    headers:
      Authorization: "Bearer ${API_TOKEN}"
```

### 2. Session Cookie Authentication

Standard for traditional web applications:

```yaml
authentication:
  - url: "https://app.example.com"
    cookies:
      session_id: "${SESSION_ID}"
      csrf_token: "${CSRF_TOKEN}"
    headers:
      X-CSRF-Token: "${CSRF_TOKEN}"
```

### 3. Basic Authentication

Legacy HTTP Basic Auth:

```yaml
authentication:
  - url: "https://admin.example.com"
    basic:
      username: "${ADMIN_USER}"
      password: "${ADMIN_PASS}"
```

### 4. API Key Authentication

Custom header-based authentication:

```yaml
authentication:
  - url: "https://internal.example.com"
    headers:
      X-API-Key: "${API_KEY}"
      X-User-ID: "${USER_ID}"
```

### 5. Combined Authentication

Multiple methods for complex scenarios:

```yaml
authentication:
  - url: "https://secure.example.com"
    headers:
      Authorization: "Bearer ${ACCESS_TOKEN}"
      X-Request-ID: "surface-discovery"
    cookies:
      session: "${SESSION_COOKIE}"
      preferences: "theme=dark"
```

## Configuration File Format

Authentication configuration uses YAML format with environment variable substitution.

### Basic Structure

```yaml
authentication:
  - url: "https://target.com"
    headers: {}      # Optional: Custom headers
    cookies: {}      # Optional: Authentication cookies
    basic:           # Optional: Basic auth credentials
      username: ""
      password: ""
```

### Environment Variable Substitution

Use `${VAR_NAME}` or `%{VAR_NAME}` syntax to reference environment variables:

```yaml
authentication:
  - url: "https://api.example.com"
    headers:
      Authorization: "Bearer ${MY_API_TOKEN}"  # Substituted at runtime
      X-API-Version: "v2"                      # Literal value
```

**Before running:**
```bash
export MY_API_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### URL Matching

The parser uses **prefix matching** for URLs:

- Config: `url: "https://app.example.com"`
- Matches:
  - `https://app.example.com/dashboard` ✅
  - `https://app.example.com/api/users` ✅
  - `https://api.example.com/v1/data` ❌ (different subdomain)

For exact matching, specify the full path:
```yaml
- url: "https://app.example.com/api/v1"  # Only matches this path
```

### Complete Example Configuration

```yaml
# auth-config.yaml
authentication:
  # Production API with JWT
  - url: "https://api.example.com"
    headers:
      Authorization: "Bearer ${PROD_API_TOKEN}"
      X-API-Version: "v2"
      X-Request-ID: "pentest-2024"

  # Web application with session cookies
  - url: "https://app.example.com"
    cookies:
      session_id: "${APP_SESSION_ID}"
      csrf_token: "${APP_CSRF_TOKEN}"
      remember_me: "true"
    headers:
      X-CSRF-Token: "${APP_CSRF_TOKEN}"

  # Admin panel with basic auth
  - url: "https://admin.example.com"
    basic:
      username: "${ADMIN_USERNAME}"
      password: "${ADMIN_PASSWORD}"

  # Internal services with API key
  - url: "https://internal.example.com"
    headers:
      X-API-Key: "${INTERNAL_API_KEY}"
      X-Service-Name: "surface-discovery"

  # Staging environment (multiple methods)
  - url: "https://staging.example.com"
    headers:
      Authorization: "Bearer ${STAGING_TOKEN}"
    cookies:
      session: "${STAGING_SESSION}"
    basic:
      username: "${STAGING_USER}"
      password: "${STAGING_PASS}"
```

## Docker Usage

### Step 1: Create Authentication Config

Save your auth configuration to `input/auth-config.yaml`:

```yaml
authentication:
  - url: "https://example.com"
    headers:
      Authorization: "Bearer ${API_TOKEN}"
    cookies:
      session: "${SESSION_ID}"
```

### Step 2: Set Environment Variables

Export your credentials:

```bash
export API_TOKEN="your-jwt-token-here"
export SESSION_ID="your-session-cookie"
export CSRF_TOKEN="your-csrf-token"
```

### Step 3: Run Authenticated Scan

**Basic authenticated scan:**

```bash
docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  -e API_TOKEN \
  -e SESSION_ID \
  surface-discovery:latest \
  --url https://example.com \
  --auth-mode \
  --auth-config /input/auth-config.yaml \
  --output /output/results.json
```

**With all options:**

```bash
docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  -e API_TOKEN \
  -e SESSION_ID \
  -e CSRF_TOKEN \
  surface-discovery:latest \
  --url https://example.com \
  --depth deep \
  --timeout 900 \
  --parallel 15 \
  --auth-mode \
  --auth-config /input/auth-config.yaml \
  --output /output/auth-scan.json \
  --verbose
```

### Docker Volume Mounts

- `-v $(pwd)/input:/input` - Mount local `input/` directory to container's `/input`
- `-v $(pwd)/output:/output` - Mount local `output/` directory for results
- Auth config path inside container: `/input/auth-config.yaml`

### Environment Variable Passing

Pass each credential individually:

```bash
-e VAR_NAME              # Pass variable from host environment
-e VAR_NAME=value        # Set variable explicitly
```

**Example with multiple variables:**

```bash
docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  -e API_TOKEN \
  -e SESSION_ID \
  -e CSRF_TOKEN \
  -e ADMIN_USER \
  -e ADMIN_PASS \
  surface-discovery:latest \
  --url https://example.com \
  --auth-mode \
  --auth-config /input/auth-config.yaml
```

## Local Usage

### Step 1: Create Authentication Config

Create `config/auth.yaml`:

```yaml
authentication:
  - url: "https://example.com"
    headers:
      Authorization: "Bearer ${API_TOKEN}"
```

### Step 2: Set Environment Variables

```bash
export API_TOKEN="your-token-here"
export SESSION_ID="your-session"
```

### Step 3: Run Local Scan

```bash
python cli.py \
  --url https://example.com \
  --auth-mode \
  --auth-config config/auth.yaml \
  --output results.json \
  --depth normal \
  --verbose
```

## Security Best Practices

### 1. Environment Variables

✅ **DO:**
- Use environment variables for all sensitive credentials
- Use meaningful variable names (e.g., `PROD_API_TOKEN`, not `TOKEN1`)
- Document required variables in README or deployment docs

❌ **DON'T:**
- Hardcode credentials directly in YAML files
- Commit auth files with real credentials to version control
- Share environment variables in chat/email

### 2. Credential Management

✅ **DO:**
- Rotate credentials after penetration testing
- Use read-only or limited-scope credentials when possible
- Create dedicated test accounts for scanning
- Set credential expiration timeframes

❌ **DON'T:**
- Use production admin credentials
- Reuse personal account credentials
- Share credentials across multiple tools/teams

### 3. File Security

✅ **DO:**
- Add auth config files to `.gitignore`
- Set restrictive file permissions (`chmod 600 auth-config.yaml`)
- Store configs in secure locations (encrypted volumes)
- Delete or sanitize configs after testing

❌ **DON'T:**
- Commit auth configs to public repositories
- Store configs in shared directories
- Leave credentials in Docker volumes after testing

### 4. Session Cleanup

After scanning, clean up:

```bash
# Unset environment variables
unset API_TOKEN SESSION_ID CSRF_TOKEN ADMIN_USER ADMIN_PASS

# Remove temporary auth files
rm -f /tmp/auth-*.yaml

# Clear shell history if needed (bash)
history -c
```

### 5. Scope Limitation

✅ **DO:**
- Create test accounts with minimal necessary permissions
- Use separate staging/test environments when possible
- Configure rate limiting for test accounts
- Monitor account activity during scanning

❌ **DON'T:**
- Grant full admin access to test accounts
- Run authenticated scans against production without approval
- Disable security controls for testing convenience

## Troubleshooting

### Error: "Environment variable 'X' not found"

**Cause:** Referenced environment variable is not set.

**Solution:**
```bash
# Check if variable is set
echo $API_TOKEN

# Set the variable
export API_TOKEN="your-token-here"

# Verify it's set
env | grep API_TOKEN
```

### Error: "Auth config not found"

**Cause:** Path to auth config file is incorrect.

**Solution:**
```bash
# For Docker: Ensure volume mount is correct
-v $(pwd)/input:/input

# Verify file exists in container
docker run --rm -v $(pwd)/input:/input surface-discovery ls -la /input/

# For local: Use absolute or relative path
python cli.py --auth-config /absolute/path/to/auth.yaml
python cli.py --auth-config ./config/auth.yaml
```

### Error: "Invalid YAML in auth config"

**Cause:** YAML syntax error in config file.

**Solution:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('input/auth-config.yaml'))"

# Common issues:
# - Missing quotes around values with special characters
# - Incorrect indentation (use spaces, not tabs)
# - Missing colons or hyphens
```

### Authentication Not Working

**Symptoms:** Scan completes but authenticated areas not discovered.

**Debug steps:**

1. **Verify credentials are valid:**
   ```bash
   # Test API token manually
   curl -H "Authorization: Bearer $API_TOKEN" https://api.example.com/user
   ```

2. **Check URL matching:**
   ```yaml
   # Ensure URL prefix matches your target
   - url: "https://app.example.com"  # Matches app.example.com/*
   - url: "https://api.example.com"  # Doesn't match app.example.com
   ```

3. **Enable verbose logging:**
   ```bash
   docker run ... --verbose
   ```

4. **Verify environment variables in container:**
   ```bash
   docker run ... -e API_TOKEN env | grep API_TOKEN
   ```

### Scan Hangs or Times Out

**Cause:** Authenticated crawling may take longer.

**Solution:**
```bash
# Increase timeout
docker run ... --timeout 1200  # 20 minutes

# Reduce crawl depth
docker run ... --depth shallow

# Limit concurrent requests
docker run ... --parallel 5
```

## Examples

### Example 1: SPA with JWT Authentication

**Scenario:** React app with JWT token stored in localStorage.

**Get credentials:**
1. Login to application in browser
2. Open DevTools → Application → Local Storage
3. Copy JWT token value

**Config (`input/spa-auth.yaml`):**
```yaml
authentication:
  - url: "https://app.example.com"
    headers:
      Authorization: "Bearer ${SPA_JWT_TOKEN}"
      X-Requested-With: "XMLHttpRequest"
```

**Run:**
```bash
export SPA_JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  -e SPA_JWT_TOKEN \
  surface-discovery:latest \
  --url https://app.example.com \
  --auth-mode \
  --auth-config /input/spa-auth.yaml \
  --output /output/spa-scan.json
```

### Example 2: Traditional Web App with Session Cookies

**Scenario:** PHP/Django app with session cookies.

**Get credentials:**
1. Login to application in browser
2. Open DevTools → Application → Cookies
3. Copy `PHPSESSID` (or `sessionid`) and `csrftoken` values

**Config (`input/webapp-auth.yaml`):**
```yaml
authentication:
  - url: "https://www.example.com"
    cookies:
      PHPSESSID: "${PHP_SESSION}"
      csrftoken: "${CSRF_TOKEN}"
    headers:
      X-CSRFToken: "${CSRF_TOKEN}"
      Referer: "https://www.example.com"
```

**Run:**
```bash
export PHP_SESSION="abc123def456ghi789"
export CSRF_TOKEN="xyz789abc123def456"

docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  -e PHP_SESSION \
  -e CSRF_TOKEN \
  surface-discovery:latest \
  --url https://www.example.com \
  --auth-mode \
  --auth-config /input/webapp-auth.yaml \
  --depth normal \
  --output /output/webapp-scan.json
```

### Example 3: API with Multiple Authentication Methods

**Scenario:** Microservices architecture with different auth per service.

**Config (`input/microservices-auth.yaml`):**
```yaml
authentication:
  # User service - JWT
  - url: "https://user.api.example.com"
    headers:
      Authorization: "Bearer ${USER_SERVICE_TOKEN}"
      X-Service-Name: "surface-discovery"

  # Payment service - API Key
  - url: "https://payment.api.example.com"
    headers:
      X-API-Key: "${PAYMENT_API_KEY}"
      X-Merchant-ID: "${MERCHANT_ID}"

  # Admin service - Basic Auth
  - url: "https://admin.api.example.com"
    basic:
      username: "${ADMIN_USER}"
      password: "${ADMIN_PASS}"

  # Legacy service - Session Cookie
  - url: "https://legacy.api.example.com"
    cookies:
      legacy_session: "${LEGACY_SESSION}"
```

**Run:**
```bash
# Set all credentials
export USER_SERVICE_TOKEN="jwt-token-here"
export PAYMENT_API_KEY="api-key-here"
export MERCHANT_ID="merchant-123"
export ADMIN_USER="admin"
export ADMIN_PASS="password"
export LEGACY_SESSION="legacy-session-id"

# Run scan
docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  -e USER_SERVICE_TOKEN \
  -e PAYMENT_API_KEY \
  -e MERCHANT_ID \
  -e ADMIN_USER \
  -e ADMIN_PASS \
  -e LEGACY_SESSION \
  surface-discovery:latest \
  --url https://api.example.com \
  --auth-mode \
  --auth-config /input/microservices-auth.yaml \
  --depth deep \
  --output /output/microservices-scan.json \
  --verbose
```

### Example 4: GraphQL API with Bearer Token

**Scenario:** GraphQL API requiring authentication header.

**Config (`input/graphql-auth.yaml`):**
```yaml
authentication:
  - url: "https://graphql.example.com"
    headers:
      Authorization: "Bearer ${GRAPHQL_TOKEN}"
      Content-Type: "application/json"
      X-Request-ID: "surface-discovery-scan"
```

**Run:**
```bash
export GRAPHQL_TOKEN="your-graphql-jwt-token"

docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  -e GRAPHQL_TOKEN \
  surface-discovery:latest \
  --url https://graphql.example.com \
  --auth-mode \
  --auth-config /input/graphql-auth.yaml \
  --output /output/graphql-scan.json
```

## Additional Resources

- [Main README](../README.md) - General usage and installation
- [Docker Documentation](DOCKER.md) - Detailed Docker usage
- [Configuration Reference](CONFIGURATION.md) - All configuration options
- [Output Format](OUTPUT_FORMAT.md) - Understanding scan results

## Quick Reference

### Required Flags

- `--auth-mode` - Enable authenticated scanning
- `--auth-config <path>` - Path to auth configuration file

### Optional Flags (Recommended)

- `--depth <shallow|normal|deep>` - Scan depth (affects crawling)
- `--timeout <seconds>` - Maximum execution time
- `--parallel <n>` - Concurrent requests
- `--verbose` - Detailed logging
- `--skip-vuln-scan` - Skip vulnerability scanning stage

### Environment Variable Syntax

- `${VAR_NAME}` - Standard shell-style (recommended)
- `%{VAR_NAME}` - Alternative syntax

### File Paths

- **Docker**: `/input/auth-config.yaml` (inside container)
- **Local**: `./config/auth.yaml` (relative to working directory)

---

**Need help?** Open an issue at [GitHub Issues](https://github.com/your-org/surface-discovery/issues)
