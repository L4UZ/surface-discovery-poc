# Surface Discovery - Project Context

## Project Type
Proof-of-concept web attack surface reconnaissance service

## Technology Stack
- **Language**: Python 3.11
- **Security Tools**: ProjectDiscovery suite (subfinder, httpx, nuclei, katana, dnsx, naabu)
- **Async Framework**: asyncio for concurrent execution
- **Data Validation**: Pydantic v2
- **CLI Framework**: Click
- **Output**: Rich terminal UI, JSON export
- **Deployment**: Docker multi-stage build

## Core Architecture

### Discovery Pipeline (4 stages)
1. **Passive Discovery** ✅ - Subdomain enumeration, DNS resolution
2. **Active Discovery** ⏳ - Service enumeration, port scanning
3. **Deep Discovery** ⏳ - Web crawling, endpoint discovery
4. **Enrichment** ⏳ - Technology detection, vulnerability scanning

### Key Components
- **discovery/core.py**: Main orchestration engine with async pipeline
- **discovery/tools/runner.py**: Async subprocess execution wrapper
- **discovery/stages/**: Stage implementations (passive, active, deep, enrichment)
- **discovery/models/**: Pydantic data models for all result types
- **cli.py**: Rich CLI interface with Click framework

## Configuration
- **Depth Presets**: shallow (quick), normal (standard), deep (comprehensive)
- **Parallel Execution**: Configurable concurrent task limit
- **Timeouts**: Per-tool and global timeouts
- **Output**: Configurable JSON output path

## Docker Architecture
- **Build Stage**: golang:1.24-bookworm (ProjectDiscovery tools)
- **Runtime Stage**: python:3.11-slim (application execution)
- **Security**: Non-root user (discovery:1000)
- **Capabilities**: CAP_NET_RAW, CAP_NET_ADMIN for naabu

## Known Issues Resolved
1. Go version compatibility (requires 1.24+)
2. Binary compatibility (musl vs glibc)
3. Python import exports (DiscoveryStage, WHOISData)
4. CLI flag validation (--check-tools without --url)

## Development Status
- **Core Implementation**: Complete (passive discovery working)
- **Docker Packaging**: Complete and tested
- **Documentation**: Comprehensive (README, DOCKER.md, TROUBLESHOOTING.md)
- **Testing**: Manual testing complete, automated tests pending
- **Remaining Work**: Active/deep/enrichment stages (not yet requested)
