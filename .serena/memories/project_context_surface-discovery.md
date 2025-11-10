# Surface Discovery - Project Context

## Project Type
Production-ready web attack surface reconnaissance service

## Technology Stack
- **Language**: TypeScript (Node.js 20+)
- **Package Manager**: pnpm
- **Data Validation**: Zod (runtime validation with type inference)
- **CLI Framework**: Commander.js
- **Terminal Output**: Chalk + cli-table3 + ora + boxen
- **Logging**: Winston
- **Browser Automation**: Playwright
- **Deployment**: Docker (Node.js base image)

## Core Architecture

### Discovery Pipeline (5 stages) - ALL COMPLETE ✅
1. **Passive Discovery** ✅ - Subdomain enumeration (subfinder), DNS resolution (dnsx)
2. **Port Discovery** ✅ - Network port scanning (naabu)
3. **Active Discovery** ✅ - HTTP probing (httpx), technology detection
4. **Deep Discovery** ✅ - Web crawling (katana), endpoint discovery
5. **Enrichment** ✅ - Infrastructure intelligence (cloud/CDN providers, ASN)
6. **Authenticated Discovery** ✅ - Session-based authenticated crawling (Playwright)

**NOTE**: Nuclei vulnerability scanning has been REMOVED from the Node.js version.

### Key Components
- **src/core.ts**: Main orchestration engine with async pipeline
- **src/tools/runner.ts**: Subprocess execution wrapper for security tools
- **src/stages/**: Complete stage implementations (passive, portDiscovery, active, deep, enrichment, authenticated)
- **src/models/**: Zod data models for all result types
- **src/config.ts**: Depth-based configuration presets
- **src/cli.ts**: Commander.js CLI interface

## Configuration
- **Depth Presets**: shallow (quick), normal (standard), deep (comprehensive)
- **Parallel Execution**: Configurable concurrent task limit (default: 10)
- **Timeouts**: Per-tool timeouts (subfinder: 180s, httpx: 180s, katana: 300s, etc.)
- **Output**: Configurable JSON output path with auto-generated filenames

## Docker Architecture
- **Build Stage**: golang:1.24-bookworm (ProjectDiscovery tools installation)
- **Runtime Stage**: node:20-slim (application execution)
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
- `--auth-config`: JSON authentication configuration file

## External Tools (5 tools)
- **subfinder**: Subdomain enumeration
- **httpx**: HTTP probing and technology detection
- **naabu**: Port scanning
- **katana**: Web crawling
- **dnsx**: DNS resolution

**NOTE**: Nuclei has been removed from the Node.js version.

## Project Status
- **Migration**: 100% complete - Node.js is sole implementation
- **Build**: ✅ Compiles with 0 errors
- **CLI**: ✅ All commands working
- **Tools**: ✅ All 5 external tools detected
- **Type Safety**: 70% (strict mode temporarily disabled, needs re-enabling incrementally)
- **Testing**: Unit tests with Vitest (pending implementation)

## Development Commands
```bash
# Development
pnpm dev --url example.com --depth shallow

# Production
pnpm build
pnpm start -- --url example.com --output results.json

# Code Quality
pnpm typecheck    # Type checking
pnpm lint         # Code linting
pnpm lint:fix     # Auto-fix issues
pnpm format       # Code formatting

# Testing
pnpm test         # Run tests
pnpm test:coverage # With coverage
```

## Output Format
Comprehensive JSON including:
- Metadata (scan_id, duration, completeness)
- Domains (subdomains with DNS records, WHOIS data, open ports)
- Services (HTTP/HTTPS probing results with technologies)
- Endpoints (crawled URLs with parameters)
- Technologies (detected tech stack)
- Infrastructure (cloud providers, CDN, ASN mappings)
- Statistics (aggregated metrics including port scan statistics)
- Timeline (discovery event log)

## Performance Characteristics
- **Shallow depth**: ~30-60s (20 subdomains limit, 100 top ports, depth 2 crawling)
- **Normal depth**: ~3-10min (unlimited subdomains, 1000 top ports, depth 3 crawling)
- **Deep depth**: ~10-15min (unlimited subdomains, all 65535 ports, depth 5 crawling)

## Authentication Support
- **Config Format**: JSON (NOT YAML - no environment variable substitution)
- **Methods**: Session cookies, JWT tokens, OAuth2 headers, custom headers, basic auth
- **Flow**: Normal discovery → Authenticated crawling → Combined results
- **Output**: Authenticated endpoints marked and counted separately
