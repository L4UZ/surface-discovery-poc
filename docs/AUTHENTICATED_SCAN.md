# Authenticated Scanning Guide

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

When `--auth-config` is provided, the tool performs:

1. **Stage 3: Deep Discovery (Authenticated)** - Crawls authenticated endpoints using provided credentials
2. **Stage 6: Authenticated Discovery** - Additional authenticated-only surface mapping via Playwright
3. All other stages run normally with authentication context preserved

## Authentication Methods

Surface Discovery supports multiple authentication methods that can be combined:

### 1. Bearer Token / JWT Authentication

Common for modern APIs and SPAs:

```json
{
  "authentication": [
    {
      "url": "https://api.example.com",
      "headers": {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      }
    }
  ]
}
```

### 2. Session Cookie Authentication

Standard for traditional web applications:

```json
{
  "authentication": [
    {
      "url": "https://app.example.com",
      "cookies": {
        "session_id": "abc123def456",
        "csrf_token": "xyz789abc123"
      },
      "headers": {
        "X-CSRF-Token": "xyz789abc123"
      }
    }
  ]
}
```

### 3. Basic Authentication

Legacy HTTP Basic Auth:

```json
{
  "authentication": [
    {
      "url": "https://admin.example.com",
      "basic": {
        "username": "admin",
        "password": "secure-password"
      }
    }
  ]
}
```

### 4. API Key Authentication

Custom header-based authentication:

```json
{
  "authentication": [
    {
      "url": "https://internal.example.com",
      "headers": {
        "X-API-Key": "your-api-key-here",
        "X-User-ID": "user-123"
      }
    }
  ]
}
```

### 5. Combined Authentication

Multiple methods for complex scenarios:

```json
{
  "authentication": [
    {
      "url": "https://secure.example.com",
      "headers": {
        "Authorization": "Bearer token-here",
        "X-Request-ID": "surface-discovery"
      },
      "cookies": {
        "session": "session-cookie-value",
        "preferences": "theme=dark"
      }
    }
  ]
}
```

## Configuration File Format

Authentication configuration uses **JSON format** (not YAML). The Node.js implementation does not support environment variable substitution - credentials must be provided directly in the JSON file.

### Basic Structure

```json
{
  "authentication": [
    {
      "url": "https://target.com",
      "headers": {},
      "cookies": {},
      "basic": {
        "username": "",
        "password": ""
      }
    }
  ]
}
```

**All fields are optional except `url`:**
- `headers` - Custom HTTP headers (object)
- `cookies` - Authentication cookies (object)
- `basic` - Basic auth credentials (object with `username` and `password`)

### URL Matching

The parser uses **prefix matching** for URLs:

- Config: `"url": "https://app.example.com"`
- Matches:
  - `https://app.example.com/dashboard` ✅
  - `https://app.example.com/api/users` ✅
  - `https://api.example.com/v1/data` ❌ (different subdomain)

For exact matching, specify the full path:
```json
{
  "url": "https://app.example.com/api/v1"
}
```

### Complete Example Configuration

```json
{
  "authentication": [
    {
      "url": "https://api.example.com",
      "headers": {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "X-API-Version": "v2",
        "X-Request-ID": "pentest-2024"
      }
    },
    {
      "url": "https://app.example.com",
      "cookies": {
        "session_id": "abc123def456ghi789",
        "csrf_token": "xyz789abc123def456",
        "remember_me": "true"
      },
      "headers": {
        "X-CSRF-Token": "xyz789abc123def456"
      }
    },
    {
      "url": "https://admin.example.com",
      "basic": {
        "username": "admin",
        "password": "admin-password"
      }
    },
    {
      "url": "https://internal.example.com",
      "headers": {
        "X-API-Key": "internal-api-key-12345",
        "X-Service-Name": "surface-discovery"
      }
    },
    {
      "url": "https://staging.example.com",
      "headers": {
        "Authorization": "Bearer staging-token"
      },
      "cookies": {
        "session": "staging-session-id"
      },
      "basic": {
        "username": "staging-user",
        "password": "staging-pass"
      }
    }
  ]
}
```

## Docker Usage

### Step 1: Create Authentication Config

Save your auth configuration to `input/auth-config.json`:

```json
{
  "authentication": [
    {
      "url": "https://example.com",
      "headers": {
        "Authorization": "Bearer your-jwt-token-here"
      },
      "cookies": {
        "session": "your-session-cookie"
      }
    }
  ]
}
```

### Step 2: Run Authenticated Scan

**Basic authenticated scan:**

```bash
docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  surface-discovery:latest \
  --url https://example.com \
  --auth-config /input/auth-config.json \
  --output /output/results.json
```

**With all options:**

```bash
docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  surface-discovery:latest \
  --url https://example.com \
  --depth deep \
  --timeout 900 \
  --parallel 15 \
  --auth-config /input/auth-config.json \
  --output /output/auth-scan.json \
  --verbose
```

### Docker Volume Mounts

- `-v $(pwd)/input:/input` - Mount local `input/` directory to container's `/input`
- `-v $(pwd)/output:/output` - Mount local `output/` directory for results
- Auth config path inside container: `/input/auth-config.json`

## Local Usage

### Step 1: Create Authentication Config

Create `config/auth.json`:

```json
{
  "authentication": [
    {
      "url": "https://example.com",
      "headers": {
        "Authorization": "Bearer your-token-here"
      }
    }
  ]
}
```

### Step 2: Run Local Scan

**Development mode (TypeScript):**
```bash
pnpm dev --url https://example.com \
  --auth-config config/auth.json \
  --output results.json \
  --depth normal \
  --verbose
```

**Production mode (compiled):**
```bash
pnpm start -- --url https://example.com \
  --auth-config config/auth.json \
  --output results.json \
  --depth normal \
  --verbose
```

**Direct Node.js:**
```bash
node dist/cli.js --url https://example.com \
  --auth-config config/auth.json \
  --output results.json \
  --depth normal \
  --verbose
```

## Security Best Practices

### 1. Credential Storage

✅ **DO:**
- Store auth config files outside version control
- Use secure file locations (encrypted volumes, secure directories)
- Set restrictive file permissions (`chmod 600 auth-config.json`)
- Delete or sanitize configs after testing

❌ **DON'T:**
- Commit auth configs with real credentials to git
- Store configs in publicly accessible directories
- Leave credentials in Docker volumes after testing
- Share auth files via insecure channels

### 2. Credential Management

✅ **DO:**
- Rotate credentials after penetration testing
- Use read-only or limited-scope credentials when possible
- Create dedicated test accounts for scanning
- Set credential expiration timeframes
- Monitor account activity during scanning

❌ **DON'T:**
- Use production admin credentials
- Reuse personal account credentials
- Share credentials across multiple tools/teams
- Grant full admin access to test accounts

### 3. File Security

Add to `.gitignore`:
```
# Authentication configs
config/auth.json
input/auth-config.json
**/auth*.json
*.credentials.json
```

Set secure permissions:
```bash
chmod 600 config/auth.json
```

### 4. Session Cleanup

After scanning, clean up:

```bash
# Remove temporary auth files
rm -f /tmp/auth-*.json
rm -f config/auth.json

# Clear shell history if credentials were typed (bash)
history -c
history -w
```

### 5. Scope Limitation

✅ **DO:**
- Create test accounts with minimal necessary permissions
- Use separate staging/test environments when possible
- Configure rate limiting for test accounts
- Get proper authorization before scanning production

❌ **DON'T:**
- Run authenticated scans against production without approval
- Disable security controls for testing convenience
- Use credentials with write/delete permissions

## Troubleshooting

### Error: "Failed to parse auth config"

**Cause:** Invalid JSON syntax in config file.

**Solution:**
```bash
# Validate JSON syntax
node -e "console.log(JSON.parse(require('fs').readFileSync('input/auth-config.json')))"

# Or use jq
jq . input/auth-config.json

# Common issues:
# - Trailing commas (invalid in JSON)
# - Missing quotes around keys/values
# - Single quotes instead of double quotes
# - Missing closing brackets/braces
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
node dist/cli.js --auth-config /absolute/path/to/auth.json
node dist/cli.js --auth-config ./config/auth.json
```

### Authentication Not Working

**Symptoms:** Scan completes but authenticated areas not discovered.

**Debug steps:**

1. **Verify credentials are valid:**
   ```bash
   # Test API token manually
   curl -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com/user
   ```

2. **Check JSON syntax:**
   ```bash
   # Validate your JSON
   jq . config/auth.json
   ```

3. **Check URL matching:**
   ```json
   {
     "authentication": [
       {
         "url": "https://app.example.com"
       }
     ]
   }
   ```
   Matches `app.example.com/*` but NOT `api.example.com/*`

4. **Enable verbose logging:**
   ```bash
   node dist/cli.js --url https://example.com \
     --auth-config config/auth.json \
     --verbose
   ```

5. **Check file permissions:**
   ```bash
   ls -la config/auth.json
   # Should be readable by current user
   ```

### Scan Hangs or Times Out

**Cause:** Authenticated crawling may take longer.

**Solution:**
```bash
# Increase timeout (default is 120 seconds)
node dist/cli.js --timeout 1200 ...  # 20 minutes

# Reduce crawl depth
node dist/cli.js --depth shallow ...

# Limit concurrent requests
node dist/cli.js --parallel 5 ...
```

### Invalid JSON Error

**Problem:** JSON parsing fails with syntax error.

**Common mistakes:**

❌ **Wrong (trailing comma):**
```json
{
  "authentication": [
    {
      "url": "https://example.com",
      "headers": {
        "Authorization": "Bearer token",
      }
    },
  ]
}
```

✅ **Correct:**
```json
{
  "authentication": [
    {
      "url": "https://example.com",
      "headers": {
        "Authorization": "Bearer token"
      }
    }
  ]
}
```

## Examples

### Example 1: SPA with JWT Authentication

**Scenario:** React app with JWT token stored in localStorage.

**Get credentials:**
1. Login to application in browser
2. Open DevTools → Application → Local Storage
3. Copy JWT token value

**Config (`input/spa-auth.json`):**
```json
{
  "authentication": [
    {
      "url": "https://app.example.com",
      "headers": {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "X-Requested-With": "XMLHttpRequest"
      }
    }
  ]
}
```

**Run:**
```bash
docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  surface-discovery:latest \
  --url https://app.example.com \
  --auth-config /input/spa-auth.json \
  --output /output/spa-scan.json
```

### Example 2: Traditional Web App with Session Cookies

**Scenario:** PHP/Django app with session cookies.

**Get credentials:**
1. Login to application in browser
2. Open DevTools → Application → Cookies
3. Copy `PHPSESSID` (or `sessionid`) and `csrftoken` values

**Config (`input/webapp-auth.json`):**
```json
{
  "authentication": [
    {
      "url": "https://www.example.com",
      "cookies": {
        "PHPSESSID": "abc123def456ghi789",
        "csrftoken": "xyz789abc123def456"
      },
      "headers": {
        "X-CSRFToken": "xyz789abc123def456",
        "Referer": "https://www.example.com"
      }
    }
  ]
}
```

**Run:**
```bash
docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  surface-discovery:latest \
  --url https://www.example.com \
  --auth-config /input/webapp-auth.json \
  --depth normal \
  --output /output/webapp-scan.json
```

### Example 3: API with Multiple Authentication Methods

**Scenario:** Microservices architecture with different auth per service.

**Config (`input/microservices-auth.json`):**
```json
{
  "authentication": [
    {
      "url": "https://user.api.example.com",
      "headers": {
        "Authorization": "Bearer user-service-jwt-token",
        "X-Service-Name": "surface-discovery"
      }
    },
    {
      "url": "https://payment.api.example.com",
      "headers": {
        "X-API-Key": "payment-api-key-12345",
        "X-Merchant-ID": "merchant-123"
      }
    },
    {
      "url": "https://admin.api.example.com",
      "basic": {
        "username": "admin",
        "password": "admin-password"
      }
    },
    {
      "url": "https://legacy.api.example.com",
      "cookies": {
        "legacy_session": "legacy-session-id-xyz"
      }
    }
  ]
}
```

**Run:**
```bash
docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  surface-discovery:latest \
  --url https://api.example.com \
  --auth-config /input/microservices-auth.json \
  --depth deep \
  --output /output/microservices-scan.json \
  --verbose
```

### Example 4: GraphQL API with Bearer Token

**Scenario:** GraphQL API requiring authentication header.

**Config (`input/graphql-auth.json`):**
```json
{
  "authentication": [
    {
      "url": "https://graphql.example.com",
      "headers": {
        "Authorization": "Bearer your-graphql-jwt-token",
        "Content-Type": "application/json",
        "X-Request-ID": "surface-discovery-scan"
      }
    }
  ]
}
```

**Run:**
```bash
docker run --rm \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  surface-discovery:latest \
  --url https://graphql.example.com \
  --auth-config /input/graphql-auth.json \
  --output /output/graphql-scan.json
```

### Example 5: Multiple Environments

**Config (`input/multi-env-auth.json`):**
```json
{
  "authentication": [
    {
      "url": "https://staging.example.com",
      "headers": {
        "Authorization": "Bearer staging-jwt-token"
      },
      "cookies": {
        "staging_session": "staging-session-id"
      }
    },
    {
      "url": "https://dev.example.com",
      "headers": {
        "Authorization": "Bearer dev-jwt-token"
      },
      "cookies": {
        "dev_session": "dev-session-id"
      }
    }
  ]
}
```

## Additional Resources

- [Main README](../README.md) - General usage and installation
- [Quick Start Guide](QUICKSTART.md) - Getting started quickly
- [Docker Documentation](DOCKER.md) - Detailed Docker usage
- [Installation Guide](INSTALLATION.md) - Complete setup instructions

## Quick Reference

### Required Flags

- `--url <url>` - Target URL to scan
- `--auth-config <path>` - Path to JSON authentication configuration file

### Optional Flags (Recommended)

- `--depth <shallow|normal|deep>` - Scan depth (affects crawling)
- `--timeout <seconds>` - Maximum execution time (default: 120)
- `--parallel <n>` - Concurrent requests (default: 10)
- `--verbose` - Detailed logging
- `--output <path>` - Output file path (default: discovery_results.json)

### File Paths

- **Docker**: `/input/auth-config.json` (inside container)
- **Local**: `./config/auth.json` (relative to working directory)
- **Absolute**: `/absolute/path/to/auth.json`

### Configuration Format

- **Format**: JSON (not YAML)
- **Encoding**: UTF-8
- **Syntax**: Standard JSON (no trailing commas, double quotes only)
- **Validation**: Use `jq` or `node -e` to validate before use

### Development Commands

```bash
# Development mode (hot reload)
pnpm dev --url https://example.com --auth-config config/auth.json

# Production build
pnpm build
pnpm start -- --url https://example.com --auth-config config/auth.json

# Direct execution
node dist/cli.js --url https://example.com --auth-config config/auth.json
```

---

**Need help?** Open an issue at the project's GitHub repository
