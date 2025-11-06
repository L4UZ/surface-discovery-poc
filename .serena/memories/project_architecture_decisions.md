# Surface Discovery - Architecture Decisions Log

## Current Architecture (as of 2025-01-05)

### Pipeline Structure (5 Stages)

**Stage 1: Passive Discovery**
- Tool: subfinder
- Purpose: Subdomain enumeration via passive sources
- Output: List of discovered subdomains
- Implementation: discovery/stages/passive.py

**Stage 2: Port Discovery**
- Tool: naabu
- Purpose: Network port scanning
- Configuration: Depth-based (shallow=100, normal=1000, deep=full)
- Requires: Docker capabilities (--cap-add=NET_RAW --cap-add=NET_ADMIN)
- Implementation: discovery/stages/port_discovery.py
- Added: Recent feature (2024-2025)

**Stage 3: Active Discovery**
- Tool: httpx
- Purpose: HTTP/HTTPS probing and technology detection
- Output: Live services, tech stack, security headers
- Implementation: discovery/stages/active.py

**Stage 4: Deep Discovery**
- Tool: katana
- Purpose: Web crawling and endpoint enumeration
- Output: Discovered endpoints, API paths, forms
- Implementation: discovery/stages/deep.py

**Stage 5: Enrichment**
- Purpose: Infrastructure intelligence analysis
- Features: Cloud provider detection, CDN identification, ASN mapping
- Implementation: discovery/stages/enrichment.py

**Excluded: Vulnerability Scanning**
- Tool: nuclei (NOT in scope for agent migration)
- Reason: Focus is surface discovery, not exploitation
- Stage 6 exists in current codebase but excluded from agent framework

### Data Models (Pydantic v2)

**Core Models:**
- `DomainInfo` (discovery/models/domain.py)
- `Subdomain` with port scanning results
- `PortScanResult` for individual port data
- `DiscoveryResult` (discovery/models/discovery.py)
- `Statistics` with port metrics

### Tool Infrastructure

**ToolRunner** (discovery/tools/runner.py)
- Async subprocess wrappers for all external tools
- Methods: run_subfinder(), run_naabu(), run_httpx(), run_katana(), run_nuclei()
- Timeout management and error handling

**Parsers** (discovery/tools/parsers.py)
- Output parsing utilities for tool results
- JSON/JSONL parsing
- Data structure conversion

### Configuration System

**DiscoveryConfig** (discovery/config.py)
- Depth presets: shallow, normal, deep
- Tool-specific timeouts and rate limits
- Parallelism control

### Authentication Support

**Auth Integration:**
- YAML-based authentication configuration
- Cookie, header, and basic auth support
- Environment variable substitution
- Example: input/strike-auth.yaml

**Documentation:**
- docs/AUTHENTICATED_SCAN.md (comprehensive guide)
- Docker usage with auth mounting
- Security best practices

### Docker Deployment

**Container Requirements:**
- Base image with Go tools installed
- Capabilities: NET_RAW, NET_ADMIN (for naabu)
- Volume mounts: /input (auth), /output (results)
- Non-root user execution

## Planned Architecture (AI Agent Framework)

### Technology Stack Decisions

**Agent Framework: LangGraph**
- Decision Date: 2025-01-05
- Rationale: Graph-based state management, native Python, production-ready
- Alternatives Rejected: AutoGen (too complex), CrewAI (too opinionated), Custom ReAct (reinventing wheel)

**LLM Provider: Anthropic Claude Sonnet**
- Decision Date: 2025-01-05
- Rationale: Superior tool use, security domain expertise, cost-effective
- Cost: ~$0.30 per reconnaissance run
- Alternatives Rejected: GPT-4 (more expensive), open source (tool use quality)

**Migration Strategy: Hybrid Dual-Mode**
- Decision Date: 2025-01-05
- Rationale: Backward compatibility, safety net, gradual adoption
- CLI: --mode pipeline|agent
- Both modes share tools and data models

**Integration Protocol: MCP**
- Decision Date: 2025-01-05
- Purpose: Claude Desktop integration
- Benefit: External agent access to reconnaissance tools

### Agent Architecture Components

**Tool Abstraction Layer:**
- Location: discovery/agent/tools/
- Base class: BaseTool (discovery/agent/tools/base.py)
- Tool wrappers: SubfinderTool, NaabuTool, HttpxTool, KatanaTool
- Schemas: discovery/agent/schemas/*.json
- Registry: discovery/agent/registry.py

**Agent Core:**
- Location: discovery/agent/core.py
- Framework: LangGraph with ReAct loop
- State: discovery/agent/state.py
- Prompts: discovery/agent/prompts/

**MCP Server:**
- Location: discovery/mcp/server.py
- Handlers: discovery/mcp/handlers.py
- Protocol: JSON-RPC 2.0 over stdio

### Agent Reasoning Patterns

**1. Adaptive Discovery:**
- Context-aware tool selection
- Dynamic strategy adjustment
- Resource-aware execution

**2. Hypothesis-Driven:**
- Forms hypotheses about infrastructure
- Tests assumptions with targeted tools
- Learns from results

**3. Error Recovery:**
- Graceful failure handling
- Alternative approach selection
- Progressive degradation

**4. Progressive Enrichment:**
- Builds context incrementally
- Uses early findings to guide later stages
- Optimizes for high-value targets

## Critical Design Constraints

### Backward Compatibility
- Pipeline mode must remain functional
- Output format unchanged (DiscoveryResult JSON)
- All existing features preserved
- No breaking changes to CLI (except new --mode flag)

### Performance Requirements
- Agent mode within 2x of pipeline performance
- Token usage < 100K per reconnaissance run
- Memory efficient state management
- Graceful degradation under load

### Security Constraints
- No unsafe decisions by agent
- Rate limiting enforced
- Sandbox isolation for tool execution
- Credential handling unchanged

### Cost Constraints
- LLM API costs < $1 per reconnaissance run target
- No infrastructure cost increase
- Development budget: $40,000
- Operational budget: $30/month

## Future Considerations

### Phase 6 (Post-Launch)
- Advanced memory and learning
- Multi-target orchestration
- Custom tool development framework
- Agent collaboration patterns

### Potential Enhancements
- Real-time streaming results
- Interactive agent mode
- Visual workflow builder
- Agent performance analytics

## References

- Migration Plan: docs/AGENT_MIGRATION_PLAN.md
- Quick Start: docs/AGENT_QUICKSTART.md
- Summary: docs/AGENT_FRAMEWORK_SUMMARY.md
- Auth Guide: docs/AUTHENTICATED_SCAN.md
