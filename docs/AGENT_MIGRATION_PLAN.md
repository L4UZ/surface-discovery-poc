# Surface Discovery → AI Agent Framework Migration Plan

**Version:** 1.1 (Updated with Phase 0: Deep URL Discovery)
**Timeline:** 13 weeks (3.25 months)
**Status:** Planning Phase

## Executive Summary

This document outlines the migration strategy to transform Surface Discovery from a deterministic 5-stage reconnaissance pipeline into an intelligent AI agent framework with autonomous tool selection and reasoning capabilities.

**Important**: This migration focuses on **surface discovery only** - vulnerability scanning (nuclei) is excluded from the agent framework scope.

### Migration Goals

1. **Enable Autonomous Operation** - AI agents can independently plan and execute reconnaissance based on high-level goals
2. **Maintain Backward Compatibility** - Existing pipeline mode continues to work unchanged
3. **MCP Integration** - Expose reconnaissance tools via MCP protocol for Claude Desktop integration
4. **Production Ready** - Agent mode achieves production-grade reliability, performance, and cost efficiency

### Key Benefits

- **Flexibility**: Agents adapt reconnaissance strategy based on target characteristics
- **Efficiency**: Skip unnecessary stages, focus on high-value targets
- **Intelligence**: Learn from past sessions, improve over time
- **Integration**: Work seamlessly with Claude Desktop and other AI tools
- **Extensibility**: Easy to add new tools and capabilities

## Current Architecture

### Pipeline Mode (Current)

```
User Input → CLI
              ↓
         DiscoveryEngine (orchestrator)
              ↓
    ┌─────────┴─────────┬─────────┬──────────┬────────────┐
    ↓                   ↓         ↓          ↓            ↓
Stage 1:            Stage 2:    Stage 3:   Stage 4:   Stage 5:
Passive             Port        Active     Deep       Enrichment
Discovery           Discovery   Discovery  Discovery  (analysis)
(subfinder)         (naabu)     (httpx)    (katana)
    ↓                   ↓         ↓          ↓            ↓
    └─────────┬─────────┴─────────┴──────────┴────────────┘
              ↓
         JSON Results
```

**Note**: Vulnerability scanning (nuclei/Stage 6) is excluded from agent framework - focus is surface discovery only.

**Characteristics:**
- ✅ Deterministic: Same inputs → same outputs
- ✅ Reliable: Well-tested, predictable behavior
- ✅ Fast: No LLM overhead
- ❌ Inflexible: Always runs all stages regardless of target
- ❌ No learning: Cannot adapt based on findings
- ❌ Manual configuration: User must set depth, timeouts, etc.

## Target Architecture

### Agent Mode (Target)

```
User Goal → CLI
             ↓
        AgentEngine
             ↓
    ┌────────┴────────┐
    ↓                 ↓
LLM Planning      Agent State
(Claude API)      (LangGraph)
    ↓                 ↓
Tool Selection ←──────┘
    ↓
    ├─→ subfinder_enumerate
    ├─→ naabu_scan
    ├─→ httpx_probe
    ├─→ katana_crawl (fast)
    ├─→ deep_crawler (comprehensive, Phase 0)
    ├─→ dnsx_resolve (optional)
    └─→ [custom tools]
         ↓
    Reflection & Learning
         ↓
    JSON Results + Reasoning Trace
```

**Characteristics:**
- ✅ Autonomous: Agent decides which tools to use and when
- ✅ Adaptive: Changes strategy based on findings
- ✅ Learning: Improves over time from experience
- ✅ Flexible: Can handle complex, multi-step reconnaissance
- ⚠️ Non-deterministic: Same inputs may → different paths (but similar results)
- ⚠️ LLM costs: API usage costs per session
- ⚠️ Latency: Reasoning adds overhead

### Hybrid Architecture

Both modes coexist:

```
CLI → Mode Selection
       ├─→ --mode pipeline → DiscoveryEngine (current)
       ├─→ --mode agent → AgentEngine (new)
       └─→ --mode hybrid → Agent decides which pipeline stages to run
```

## Migration Phases

### Phase 0: Deep URL Discovery Enhancement (Weeks 1-2)

**Objective:** Implement comprehensive URL discovery using Playwright for modern web applications

**Rationale:**
- Modern SPAs (React, Vue, Angular) require JavaScript execution for complete crawling
- Katana provides fast basic discovery but misses dynamic/hidden URLs
- Playwright-based deep crawler finds forms, POST endpoints, and interactive elements
- Infrastructure reusable for agent framework testing (Phase 3)

**Tasks:**

1. **Set Up Playwright Infrastructure**
   - Add `playwright>=1.40.0` to requirements.txt
   - Install Playwright browsers in Docker: `RUN playwright install chromium`
   - Configure async browser pool for concurrent crawling
   - Test browser automation basics

2. **Create Deep Crawler Module**
   ```python
   # discovery/crawler/deep_crawler.py
   from playwright.async_api import async_playwright, Page
   from typing import List, Set, Dict

   class DeepURLCrawler:
       """Playwright-based deep URL discovery"""

       async def crawl(
           self,
           start_urls: List[str],
           max_depth: int = 5,
           max_urls: int = 2000,
           auth_context: Optional[Dict] = None
       ) -> Set[str]:
           """
           Comprehensive URL discovery with JavaScript execution

           Features:
           - Full JavaScript rendering
           - Form interaction and submission
           - Authentication-aware crawling
           - Smart deduplication
           - Configurable depth/breadth limits
           """
   ```

3. **Implement URL Extraction and Normalization**
   ```python
   # discovery/crawler/url_extractor.py
   class URLExtractor:
       """Extract and normalize URLs from pages"""

       def extract_from_page(self, page: Page) -> Set[str]:
           """Extract all URLs: links, forms, JavaScript navigation"""

       def extract_forms(self, page: Page) -> List[Dict]:
           """Discover forms and their POST endpoints"""

       def normalize_url(self, url: str, base_url: str) -> str:
           """Normalize and deduplicate URLs"""
   ```

4. **Create URL Discovery Models**
   ```python
   # discovery/models/url.py
   class DiscoveredURL(BaseModel):
       """Individual discovered URL"""
       url: str
       method: str = "GET"  # GET, POST, etc.
       source_page: Optional[str] = None
       depth: int = 0
       parameters: Dict[str, Any] = {}
       discovered_at: datetime = Field(default_factory=datetime.utcnow)
       response_code: Optional[int] = None
       content_type: Optional[str] = None

   class URLDiscoveryResult(BaseModel):
       """Results from URL discovery stage"""
       urls: List[DiscoveredURL] = []
       total_urls: int = 0
       unique_urls: int = 0
       crawl_depth_reached: int = 0
       pages_visited: int = 0
       forms_discovered: int = 0
   ```

5. **Enhance Stage 4: Deep Discovery**
   ```python
   # discovery/stages/deep.py (updated)
   class DeepDiscovery:
       """Enhanced deep discovery with intelligent crawler selection"""

       async def run(self, subdomains: List[Subdomain]) -> DeepDiscoveryResults:
           """
           Intelligent crawling based on depth configuration:
           - shallow: katana only (fast)
           - normal: katana only (medium)
           - deep: katana + Playwright (comprehensive)
           """
           if self.config.depth == "deep":
               # Use both: katana for speed, Playwright for depth
               katana_urls = await self._run_katana(live_urls)
               playwright_urls = await self._run_deep_crawler(live_urls)
               return merge_results(katana_urls, playwright_urls)
           else:
               # Use katana only for speed
               return await self._run_katana(live_urls)
   ```

6. **Update Configuration**
   ```python
   # discovery/config.py (additions)
   class DiscoveryConfig(BaseModel):
       # ... existing fields ...

       # Deep crawling configuration
       max_crawl_depth: int = Field(default=3)
       max_urls_per_domain: int = Field(default=500)
       form_interaction: bool = Field(default=False)
       javascript_execution: bool = Field(default=False)
       crawl_timeout: int = Field(default=600)

   DEPTH_CONFIGS = {
       "shallow": DiscoveryConfig(
           max_crawl_depth=2,
           max_urls_per_domain=100,
           form_interaction=False,
           javascript_execution=False,
           crawl_timeout=300,
           # ... existing shallow config ...
       ),
       "normal": DiscoveryConfig(
           max_crawl_depth=3,
           max_urls_per_domain=500,
           form_interaction=False,
           javascript_execution=False,
           crawl_timeout=600,
           # ... existing normal config ...
       ),
       "deep": DiscoveryConfig(
           max_crawl_depth=5,
           max_urls_per_domain=2000,
           form_interaction=True,
           javascript_execution=True,
           crawl_timeout=1200,
           # ... existing deep config ...
       ),
   }
   ```

7. **Update Data Models**
   ```python
   # discovery/models/domain.py (additions)
   class Subdomain(BaseModel):
       # ... existing fields ...

       # URL discovery results
       discovered_urls: List[DiscoveredURL] = Field(default_factory=list)
       url_count: int = Field(default=0)
       forms_found: int = Field(default=0)

   # discovery/models/discovery.py (additions)
   class Statistics(BaseModel):
       # ... existing fields ...

       # URL discovery metrics
       total_urls_discovered: int = Field(default=0)
       unique_endpoints: int = Field(default=0)
       forms_found: int = Field(default=0)
   ```

8. **Authentication Integration**
   - Reuse existing auth config (input/strike-auth.yaml)
   - Pass cookies/headers to Playwright browser context
   - Support authenticated crawling seamlessly

9. **Docker Image Updates**
   ```dockerfile
   # Dockerfile (additions)
   # Install Playwright and browsers
   RUN pip install playwright>=1.40.0
   RUN playwright install chromium --with-deps

   # Playwright browsers add ~300MB to image
   ```

10. **Testing and Documentation**
    - Unit tests for URL extractor
    - Integration tests with sample SPAs
    - Performance benchmarks (katana vs Playwright)
    - Update README.md with deep crawling features
    - Document depth configuration options

**Deliverables:**
- `discovery/crawler/deep_crawler.py` - Playwright-based crawler
- `discovery/crawler/url_extractor.py` - URL extraction utilities
- `discovery/models/url.py` - URL discovery models
- Updated `discovery/stages/deep.py` - Hybrid crawler selection
- Updated `discovery/config.py` - Crawl configuration
- Updated `discovery/models/domain.py` - Subdomain with URLs
- Updated `discovery/models/discovery.py` - Statistics with URL metrics
- Updated `Dockerfile` - Playwright installation
- `tests/crawler/` - Comprehensive tests
- `docs/DEEP_URL_DISCOVERY.md` - Feature documentation

**Success Criteria:**
- ✅ Playwright successfully discovers URLs in modern SPAs
- ✅ Hybrid approach (katana + Playwright) works in deep mode
- ✅ Form discovery and interaction functional
- ✅ Authentication context properly passed to browser
- ✅ Performance acceptable (<20 minutes for deep mode on medium targets)
- ✅ Docker image builds successfully with Playwright
- ✅ Depth configuration correctly activates appropriate crawler

**Cost Impact:**
- Development: 2 weeks, 80 hours @ $100/hr = **$8,000**
- Docker image size: +300MB (Playwright browsers)
- Operational: Marginal (only used in deep mode)

**Timeline Impact:**
- Adds 2 weeks to overall migration (now 13 weeks total)

**Synergy with Agent Framework:**
- Playwright infrastructure reusable for Phase 3 (MCP Server testing)
- Deep crawler becomes 5th tool for agent (DeepCrawlerTool)
- Richer URL data improves agent decision-making quality
- Accelerates Phase 3 implementation by providing browser automation foundation

---

### Phase 1: Tool Abstraction Layer (Weeks 3-4)

**Objective:** Create standardized tool interface for agent use (now includes 5 tools)

**Tasks:**

1. **Define Tool Schemas**
   ```python
   # discovery/agent/schemas/subfinder.json
   {
     "name": "subfinder_enumerate",
     "description": "Enumerate subdomains using passive sources",
     "parameters": {
       "domain": {"type": "string", "required": true},
       "sources": {"type": "array", "items": "string", "optional": true},
       "timeout": {"type": "integer", "default": 180}
     },
     "returns": {
       "subdomains": {"type": "array", "items": "string"},
       "sources_used": {"type": "array", "items": "string"}
     }
   }
   ```

2. **Create Tool Wrappers**
   ```python
   # discovery/agent/tools/subdomain_enum.py
   from typing import List, Dict
   from ..schemas import SubfinderInput, SubfinderOutput

   class SubfinderTool:
       """Subdomain enumeration tool wrapper"""

       async def execute(self, params: SubfinderInput) -> SubfinderOutput:
           """Execute subfinder with validation and error handling"""
           # Validate inputs
           # Call ToolRunner.run_subfinder()
           # Parse and structure output
           # Return standardized result
   ```

3. **Build Tool Registry**
   ```python
   # discovery/agent/registry.py
   class ToolRegistry:
       """Central registry for all reconnaissance tools"""

       def __init__(self):
           self.tools = {
               "subfinder_enumerate": SubfinderTool(),
               "naabu_scan": NaabuTool(),
               "httpx_probe": HttpxTool(),
               "katana_crawl": KatanaTool(),
               "deep_crawler": DeepCrawlerTool(),  # NEW from Phase 0
               # Optional: "dnsx_resolve": DnsxTool()
           }
           # Note: nuclei_scan excluded - vulnerability scanning not in scope

       def get_tool(self, name: str) -> BaseTool:
           """Get tool by name"""

       def list_tools(self) -> List[Dict]:
           """List all available tools with metadata"""
   ```

**Deliverables:**
- `discovery/agent/tools/` - 6-8 tool wrapper modules
- `discovery/agent/schemas/` - JSON schemas for all tools
- `discovery/agent/registry.py` - Tool registry and discovery
- `tests/agent/test_tools.py` - Unit tests for each tool
- `docs/TOOL_CATALOG.md` - Tool documentation

**Dependencies:**
```
# requirements.txt additions
pydantic>=2.0  # Already have
jsonschema>=4.0
```

**Success Criteria:**
- ✅ All 6 reconnaissance tools wrapped with standardized interface
- ✅ 100% unit test coverage for tool wrappers
- ✅ JSON schemas validate correctly
- ✅ Tool registry can discover and instantiate all tools

---

### Phase 2: Agent Core Implementation (Weeks 3-4)

**Objective:** Build autonomous agent with LLM-powered reasoning

**Tasks:**

1. **Set Up LangGraph Framework**
   ```python
   # discovery/agent/core.py
   from langgraph.graph import StateGraph, END
   from langchain_anthropic import ChatAnthropic

   class ReconAgent:
       """Autonomous reconnaissance agent"""

       def __init__(self, goal: str):
           self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
           self.state = AgentState(goal=goal)
           self.graph = self._build_graph()

       def _build_graph(self) -> StateGraph:
           """Build agent reasoning graph"""
           graph = StateGraph(AgentState)

           # Define nodes
           graph.add_node("observe", self._observe)
           graph.add_node("plan", self._plan)
           graph.add_node("execute", self._execute)
           graph.add_node("reflect", self._reflect)

           # Define edges (flow)
           graph.add_edge("observe", "plan")
           graph.add_conditional_edges("plan", self._should_execute)
           graph.add_edge("execute", "reflect")
           graph.add_conditional_edges("reflect", self._should_continue)

           return graph.compile()
   ```

2. **Implement ReAct Reasoning Loop**
   ```python
   async def _plan(self, state: AgentState) -> AgentState:
       """Agent decides next action using LLM"""
       prompt = f"""
       Goal: {state.goal}
       Current findings: {state.findings}
       Available tools: {state.available_tools}

       Based on the goal and findings so far, what should we do next?
       Select ONE tool to use and specify parameters.

       Think step by step:
       1. What have we learned so far?
       2. What information is still missing?
       3. Which tool would best fill that gap?
       4. What parameters should we use?
       """

       response = await self.llm.ainvoke(prompt, tools=state.available_tools)
       state.next_action = response.tool_calls[0]
       return state
   ```

3. **Create Prompt Engineering System**
   ```python
   # discovery/agent/prompts/reconnaissance.py
   SYSTEM_PROMPT = """
   You are a professional penetration tester conducting reconnaissance.
   Your goal is to map the attack surface of a target domain.

   You have access to these tools:
   - subfinder_enumerate: Find subdomains using passive sources
   - naabu_scan: Scan ports on discovered hosts
   - httpx_probe: Probe HTTP/HTTPS services and detect technologies
   - katana_crawl: Fast web crawling for endpoints (static sites)
   - deep_crawler: Comprehensive crawling with JavaScript execution (SPAs, forms)
   - dnsx_resolve: Resolve DNS records (optional)

   Key principles:
   - Start with passive reconnaissance (subfinder, dnsx)
   - Progressively get more active (httpx, naabu, katana/deep_crawler)
   - Choose crawler wisely: katana for speed, deep_crawler for completeness
   - Use deep_crawler for modern SPAs (React, Vue, Angular) and form discovery
   - Adapt based on findings (if no subdomains, focus on main domain)
   - Respect rate limits and be stealthy
   - Focus on attack surface discovery, not vulnerability exploitation
   - Build comprehensive asset inventory before deep enumeration

   Always explain your reasoning before selecting a tool.
   """
   ```

4. **Build Memory and Context Management**
   ```python
   # discovery/agent/memory.py
   from typing import Dict, List

   class AgentMemory:
       """Manages agent context and learning"""

       def __init__(self):
           self.short_term = {}  # Current session
           self.long_term = {}   # Learned patterns
           self.checkpoints = [] # Resume capability

       async def save_checkpoint(self, state: AgentState):
           """Save checkpoint for resume"""

       async def load_checkpoint(self, checkpoint_id: str) -> AgentState:
           """Load previous session"""

       async def learn_pattern(self, pattern: Dict):
           """Store successful reconnaissance pattern"""
   ```

**Deliverables:**
- `discovery/agent/core.py` - Main agent implementation
- `discovery/agent/state.py` - Agent state management
- `discovery/agent/prompts/` - Prompt template library
- `discovery/agent/memory.py` - Context and learning
- `tests/agent/test_reasoning.py` - Agent logic tests
- `docs/AGENT_ARCHITECTURE.md` - Architecture documentation

**Dependencies:**
```
# requirements.txt additions
langgraph>=0.0.40
langchain>=0.1.0
langchain-anthropic>=0.1.0
anthropic>=0.18.0
```

**Success Criteria:**
- ✅ Agent can autonomously select and execute tools
- ✅ ReAct loop completes successfully for simple goals
- ✅ Checkpointing and resume works correctly
- ✅ Agent reasoning is logged and traceable

---

### Phase 3: MCP Server Implementation (Weeks 5-6)

**Objective:** Expose tools via MCP protocol for external integration

**Tasks:**

1. **Build MCP Server Infrastructure**
   ```python
   # discovery/mcp/server.py
   from mcp.server import Server
   from mcp.types import Tool, TextContent

   class SurfaceDiscoveryMCP(Server):
       """MCP server exposing reconnaissance tools"""

       def __init__(self):
           super().__init__("surface-discovery")
           self.registry = ToolRegistry()

       async def list_tools(self) -> List[Tool]:
           """List available reconnaissance tools"""
           tools = []
           for name, tool in self.registry.tools.items():
               tools.append(Tool(
                   name=name,
                   description=tool.description,
                   inputSchema=tool.schema
               ))
           return tools

       async def call_tool(self, name: str, arguments: dict) -> List[TextContent]:
           """Execute a reconnaissance tool"""
           tool = self.registry.get_tool(name)
           result = await tool.execute(arguments)
           return [TextContent(
               type="text",
               text=json.dumps(result, indent=2)
           )]
   ```

2. **Implement Tool Execution with Progress**
   ```python
   async def call_tool_streaming(self, name: str, arguments: dict):
       """Execute tool with progress streaming"""
       tool = self.registry.get_tool(name)

       async for progress in tool.execute_streaming(arguments):
           yield {
               "type": "progress",
               "percentage": progress.percentage,
               "message": progress.message
           }

       yield {
           "type": "result",
           "data": progress.final_result
       }
   ```

3. **Add Resource Management**
   ```python
   async def list_resources(self) -> List[Resource]:
       """List available resources (results, templates)"""
       return [
           Resource(
               uri="results://latest",
               name="Latest Scan Results",
               mimeType="application/json"
           ),
           Resource(
               uri="template://recon-goals",
               name="Reconnaissance Goal Templates",
               mimeType="text/markdown"
           )
       ]
   ```

4. **Claude Desktop Configuration**
   ```json
   {
     "mcpServers": {
       "surface-discovery": {
         "command": "python",
         "args": ["-m", "discovery.mcp.server"],
         "env": {
           "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
         }
       }
     }
   }
   ```

**Deliverables:**
- `discovery/mcp/server.py` - MCP server implementation
- `discovery/mcp/tools.py` - MCP tool adapters
- `discovery/mcp/resources.py` - Resource management
- `mcp-config.json` - Claude Desktop configuration
- `docs/MCP_INTEGRATION.md` - Integration guide
- `tests/mcp/test_server.py` - MCP protocol tests

**Dependencies:**
```
# requirements.txt additions
mcp>=0.1.0
```

**Success Criteria:**
- ✅ MCP server starts and registers with Claude Desktop
- ✅ All tools discoverable via list_tools
- ✅ Tool execution works from Claude Desktop
- ✅ Progress streaming functions correctly
- ✅ Resources accessible (results, templates)

---

### Phase 4: Hybrid Architecture & Migration (Weeks 7-8)

**Objective:** Enable dual-mode operation and migration tooling

**Tasks:**

1. **Implement Mode Selection**
   ```python
   # cli.py updates
   @click.option(
       '--mode',
       type=click.Choice(['pipeline', 'agent', 'hybrid']),
       default='pipeline',
       help='Execution mode: pipeline (classic), agent (autonomous), hybrid (best of both)'
   )
   async def main(url, mode, **kwargs):
       if mode == 'pipeline':
           engine = DiscoveryEngine(config)
       elif mode == 'agent':
           engine = AgentEngine(goal=f"Reconnaissance of {url}", config=config)
       else:  # hybrid
           engine = HybridEngine(config)

       results = await engine.discover(url)
   ```

2. **Create AgentEngine**
   ```python
   # discovery/engines/agent.py
   class AgentEngine:
       """Agent-based reconnaissance engine"""

       def __init__(self, goal: str, config: DiscoveryConfig):
           self.agent = ReconAgent(goal)
           self.config = config
           self.result = None

       async def discover(self, target: str) -> DiscoveryResult:
           """Execute autonomous reconnaissance"""
           # Initialize agent with goal
           # Run agent loop until goal achieved or timeout
           # Convert agent findings to DiscoveryResult format
           # Ensure backward compatible JSON output
   ```

3. **Build Hybrid Mode**
   ```python
   # discovery/engines/hybrid.py
   class HybridEngine:
       """Hybrid mode: agent decides which pipeline stages to run"""

       async def discover(self, target: str) -> DiscoveryResult:
           # Agent creates high-level plan
           plan = await self.agent.create_plan(target)

           # Execute selected pipeline stages
           for stage in plan.stages:
               if stage == "passive":
                   await self._run_passive_discovery()
               elif stage == "port":
                   await self._run_port_discovery()
               # etc.

           return self.result
   ```

4. **Ensure Output Compatibility**
   ```python
   # discovery/models/discovery.py extensions
   class DiscoveryResult(BaseModel):
       # ... existing fields ...

       # Agent-specific fields (optional, only in agent mode)
       agent_reasoning: Optional[List[ReasoningStep]] = None
       tool_usage_stats: Optional[Dict[str, int]] = None
       llm_costs: Optional[float] = None
       decision_trace: Optional[List[Decision]] = None
   ```

5. **Migration Utilities**
   ```bash
   # scripts/migrate_to_agent.py
   # Converts pipeline configs to agent goal templates
   # Analyzes pipeline runs to generate agent prompts
   # Compares pipeline vs agent results
   ```

**Deliverables:**
- `discovery/engines/agent.py` - Agent-based engine
- `discovery/engines/hybrid.py` - Hybrid mode
- Updated `cli.py` with --mode flag
- `scripts/migrate_to_agent.py` - Migration tooling
- `docs/MIGRATION_GUIDE.md` - Migration documentation
- Regression test suite ensuring pipeline mode unchanged

**Success Criteria:**
- ✅ Pipeline mode works identically to before migration
- ✅ Agent mode produces compatible JSON output
- ✅ Hybrid mode successfully combines both approaches
- ✅ All existing tests pass without modification
- ✅ Performance benchmarks show acceptable overhead

---

### Phase 5: Advanced Features & Production Readiness (Weeks 9-10)

**Objective:** Production hardening and advanced capabilities

**Tasks:**

1. **Multi-Agent Orchestration**
   ```python
   # discovery/agent/orchestration.py
   class MultiAgentOrchestrator:
       """Coordinate multiple specialist agents"""

       def __init__(self):
           self.agents = {
               "subdomain_hunter": SubdomainAgent(),
               "port_scanner": PortScanAgent(),
               "vuln_analyzer": VulnAgent()
           }

       async def orchestrate(self, goal: str) -> DiscoveryResult:
           # Decompose goal into sub-goals
           # Assign to specialist agents
           # Coordinate execution (parallel/sequential)
           # Aggregate results
   ```

2. **Production Hardening**
   ```python
   # discovery/agent/safeguards.py
   class AgentSafeguards:
       """Safety controls for agent operation"""

       def __init__(self, config):
           self.max_llm_calls = config.max_llm_calls
           self.max_tool_calls = config.max_tool_calls
           self.cost_limit = config.cost_limit
           self.rate_limits = config.rate_limits

       async def check_before_action(self, action: Action) -> bool:
           """Validate action before execution"""
           # Check cost limits
           # Check rate limits
           # Validate tool parameters
           # Ensure safe operation
   ```

3. **Monitoring and Observability**
   ```python
   # discovery/agent/monitoring.py
   class AgentMonitoring:
       """Track agent performance and costs"""

       def log_decision(self, decision: Decision):
           """Log agent reasoning decisions"""

       def track_tool_usage(self, tool: str, cost: float):
           """Track tool usage and costs"""

       def generate_report(self) -> MonitoringReport:
           """Generate session performance report"""
   ```

4. **Advanced Agent Capabilities**
   ```python
   # Self-reflection
   async def reflect_on_session(self):
       """Agent evaluates its own performance"""
       prompt = f"""
       You just completed reconnaissance of {target}.
       Your actions: {self.history}
       Results: {self.findings}

       Reflect:
       1. What worked well?
       2. What could be improved?
       3. Were there wasted actions?
       4. What would you do differently next time?
       """

   # Learning from experience
   async def learn_from_session(self):
       """Store successful patterns for future use"""
       if self.session_successful():
           pattern = extract_pattern(self.history)
           await self.memory.learn_pattern(pattern)
   ```

**Deliverables:**
- `discovery/agent/orchestration.py` - Multi-agent system
- `discovery/agent/safeguards.py` - Safety controls
- `discovery/agent/monitoring.py` - Observability
- `discovery/agent/learning.py` - Self-improvement
- `docs/AGENT_ADVANCED.md` - Advanced features guide
- `docs/PRODUCTION_DEPLOYMENT.md` - Deployment guide
- Performance benchmarks and cost analysis
- Security audit and penetration testing

**Success Criteria:**
- ✅ Multi-agent orchestration improves efficiency by >20%
- ✅ Cost controls prevent budget overruns
- ✅ Monitoring provides full observability
- ✅ Agent learns and improves over time
- ✅ Production deployment is secure and reliable

---

## Technology Stack

### Core Dependencies

```yaml
Agent Framework:
  - langgraph: ^0.0.40        # Agent state management and workflows
  - langchain: ^0.1.0         # LLM abstractions and chains
  - langchain-anthropic: ^0.1.0  # Claude integration

LLM Providers:
  - anthropic: ^0.18.0        # Claude API
  - openai: ^1.0.0 (optional) # GPT-4 fallback

Tool Interface:
  - mcp: ^0.1.0               # Model Context Protocol
  - pydantic: ^2.0            # Data validation (existing)
  - jsonschema: ^4.0          # Schema validation

Existing Stack (Keep):
  - click: CLI framework
  - pyyaml: Config management
  - rich: Terminal UI
  - asyncio: Async execution
```

### Infrastructure

```yaml
Deployment:
  - Docker: Container packaging (existing)
  - docker-compose: Multi-container orchestration

Monitoring:
  - prometheus: Metrics collection
  - grafana: Dashboards
  - opentelemetry: Distributed tracing

Storage:
  - SQLite: Local session storage
  - Redis (optional): Caching and rate limiting
```

## Migration Strategy

### Gradual Rollout

**Month 1: Alpha (Weeks 1-4)**
- Internal testing only
- Tool abstraction + Agent core
- No user-facing changes
- Gather performance data

**Month 2: Beta (Weeks 5-8)**
- Opt-in via --mode agent flag
- MCP server for early adopters
- Collect user feedback
- Benchmark against pipeline

**Month 3: GA (Weeks 9-12)**
- General availability
- Documentation complete
- Production hardening
- Performance optimized

### Backward Compatibility Guarantee

```python
# Pipeline mode will NEVER be removed
# Guaranteed to work identically to v1.0

# v2.0.0 - Agent mode added
surface-discovery --url example.com  # Still works (defaults to pipeline)
surface-discovery --url example.com --mode pipeline  # Explicit pipeline
surface-discovery --url example.com --mode agent     # New agent mode

# v3.0.0 - Agent mode default (future)
surface-discovery --url example.com  # Uses agent (can still use --mode pipeline)
```

## Success Metrics

### Performance Targets

| Metric | Pipeline Mode | Agent Mode Target |
|--------|---------------|-------------------|
| Scan Accuracy | 100% (baseline) | ≥95% |
| Time to Complete | X seconds | ≤1.3X seconds |
| Cost per Scan | $0 (local tools) | <$5 (LLM costs) |
| False Positive Rate | Y% | ≤Y% |
| Coverage Completeness | Z% | ≥Z% |

### Quality Gates

- ✅ 100% backward compatibility (pipeline mode unchanged)
- ✅ Zero breaking changes to JSON output schema
- ✅ All existing tests pass without modification
- ✅ Agent mode achieves ≥95% accuracy vs pipeline
- ✅ MCP server passes protocol compliance tests
- ✅ Security audit finds no critical vulnerabilities
- ✅ Cost controls prevent runaway LLM expenses

## Risk Management

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM non-determinism affects reliability | High | Medium | Extensive prompt engineering, validation |
| Cost explosion from long sessions | High | Medium | Token budgets, cost monitoring, local fallback |
| Agent makes unsafe tool choices | Critical | Low | Tool constraints, approval gates, sandboxing |
| Performance degradation unacceptable | Medium | Low | Async execution, caching, optimization |
| Context window overflow | Medium | Medium | Smart summarization, checkpointing |

### Organizational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Users resist agent mode adoption | Medium | Medium | Clear value prop, gradual rollout, docs |
| Breaking changes disrupt workflows | High | Low | Maintain pipeline indefinitely, semantic versioning |
| Insufficient LLM API budget | Medium | Low | Cost controls, local model option |
| Security concerns about AI agents | Medium | Low | Security audit, responsible AI practices |

## Cost Analysis

### Development Costs

```
Phase 0: Deep URL Discovery - 2 weeks × 1 FTE = $8,000
Phase 1-5: Agent Framework - 10 weeks × 1 FTE = $40,000
Total Engineering time: 13 weeks (3.25 months) = $48,000

Infrastructure: Docker, CI/CD (existing)
LLM API costs (development): ~$500 for testing
Playwright browsers: One-time Docker image size increase (+300MB)

Total Development Cost: $48,500
```

### Operating Costs

```
Pipeline Mode (existing): $0 (local tools only)

Agent Mode (new):
- LLM API: $2-5 per full scan (depends on target size)
- Infrastructure: Minimal (same Docker containers)
- Monitoring: $0 (self-hosted Prometheus/Grafana)

Cost Controls:
- Token budgets prevent overruns
- Local model fallback for high-volume use
- Caching reduces redundant LLM calls
```

### ROI

```
Benefits:
+ Autonomous operation (reduced manual configuration)
+ Better target adaptation (improved results quality)
+ Learning over time (increasing efficiency)
+ MCP integration (broader ecosystem compatibility)

Costs:
- $2-5 per agent-mode scan (LLM API)
- Development time (one-time investment)

Break-even: ~100 scans (development cost amortized)
```

## Testing Strategy

### Unit Tests

```python
# Test each component in isolation
tests/agent/
├── test_tools.py          # Tool wrappers
├── test_reasoning.py      # Agent logic
├── test_memory.py         # Context management
└── test_safeguards.py     # Safety controls

tests/mcp/
├── test_server.py         # MCP protocol
├── test_tools.py          # Tool adapters
└── test_resources.py      # Resource management
```

### Integration Tests

```python
# Test end-to-end workflows
tests/integration/
├── test_pipeline_mode.py      # Ensure unchanged
├── test_agent_mode.py         # Agent workflows
├── test_hybrid_mode.py        # Hybrid operation
└── test_mcp_integration.py    # Claude Desktop integration
```

### Performance Benchmarks

```python
# Compare pipeline vs agent mode
tests/benchmarks/
├── test_speed.py              # Time to complete
├── test_accuracy.py           # Result quality
├── test_cost.py               # LLM API costs
└── test_resource_usage.py     # Memory, CPU
```

### Security Testing

```
- Agent safety: Ensure tools used responsibly
- Input validation: Prevent injection attacks
- API key security: Proper secret management
- Rate limiting: Prevent abuse
- Audit logging: Track all agent actions
```

## Documentation Plan

### User Documentation

```
docs/
├── AGENT_MODE.md              # Getting started with agents
├── AGENT_ADVANCED.md          # Advanced features
├── MCP_INTEGRATION.md         # Claude Desktop setup
├── MIGRATION_GUIDE.md         # Pipeline → agent migration
├── TOOL_CATALOG.md            # Available tools reference
└── FAQ.md                     # Common questions
```

### Developer Documentation

```
docs/dev/
├── AGENT_ARCHITECTURE.md      # System design
├── TOOL_DEVELOPMENT.md        # Adding new tools
├── PROMPT_ENGINEERING.md      # LLM prompt guide
├── TESTING_GUIDE.md           # Test writing
└── CONTRIBUTING.md            # Contribution guidelines
```

### Examples and Tutorials

```
examples/
├── notebooks/
│   ├── 01_basic_agent.ipynb       # Simple agent usage
│   ├── 02_custom_goals.ipynb      # Goal templates
│   └── 03_multi_agent.ipynb       # Multi-agent orchestration
├── prompts/
│   ├── recon_goals.md             # Goal templates
│   └── custom_prompts.md          # Custom prompts
└── case_studies/
    ├── ecommerce_recon.md         # E-commerce target
    └── api_discovery.md           # API reconnaissance
```

## Timeline and Milestones

### Week-by-Week Plan

**Weeks 1-2: Tool Abstraction**
- [ ] Define JSON schemas for all tools
- [ ] Implement tool wrapper classes
- [ ] Build tool registry
- [ ] Write unit tests
- [ ] Document tool catalog

**Weeks 3-4: Agent Core**
- [ ] Set up LangGraph framework
- [ ] Implement ReAct loop
- [ ] Create prompt templates
- [ ] Build memory management
- [ ] Test agent reasoning

**Weeks 5-6: MCP Server**
- [ ] Implement MCP protocol
- [ ] Create tool adapters
- [ ] Add resource management
- [ ] Configure Claude Desktop
- [ ] Test integration

**Weeks 7-8: Hybrid Mode**
- [ ] Implement mode selection
- [ ] Create AgentEngine
- [ ] Build HybridEngine
- [ ] Ensure output compatibility
- [ ] Write migration tools

**Weeks 9-10: Production Ready**
- [ ] Multi-agent orchestration
- [ ] Safety controls
- [ ] Monitoring and observability
- [ ] Performance optimization
- [ ] Security audit

### Checkpoints

**Month 1 Review:**
- Tool abstraction complete
- Agent core functional
- Basic ReAct loop working

**Month 2 Review:**
- MCP server operational
- Claude Desktop integration working
- Hybrid mode available

**Month 3 Review:**
- Production hardening complete
- Documentation comprehensive
- Ready for general availability

## Next Steps

### Immediate Actions (This Week)

1. **Set up development environment**
   ```bash
   pip install langgraph langchain langchain-anthropic anthropic
   export ANTHROPIC_API_KEY="your-key-here"
   ```

2. **Create project structure**
   ```bash
   mkdir -p discovery/agent/{tools,schemas,prompts}
   mkdir -p discovery/engines
   mkdir -p discovery/mcp
   mkdir -p tests/agent tests/mcp
   ```

3. **Start with Phase 1 deliverables**
   - Define first tool schema (subfinder)
   - Implement first tool wrapper
   - Create tool registry skeleton

4. **Set up tracking**
   - Create GitHub project board
   - Define sprint cycles (2-week sprints)
   - Set up CI/CD for agent tests

### Dependencies to Install

```bash
# Phase 0: Deep URL Discovery
pip install playwright>=1.40.0
playwright install chromium

# Core agent framework
pip install langgraph langchain langchain-anthropic anthropic

# MCP protocol
pip install mcp

# Testing and development
pip install pytest pytest-asyncio pytest-cov
pip install black mypy ruff

# Monitoring (optional for now)
pip install prometheus-client opentelemetry-api
```

### Resources Needed

**Technical:**
- Anthropic API key (development)
- Test infrastructure (Docker)
- CI/CD pipeline (GitHub Actions)

**Human:**
- 1 senior engineer (full-time, 13 weeks)
- 1 technical writer (part-time, documentation)
- 1 security reviewer (code review)

**Budget:**
- LLM API costs: $500 (development/testing)
- Infrastructure: $0 (use existing)
- Tools/licenses: $0 (open source)
- Playwright browsers: Docker image size +300MB (one-time)

---

## Conclusion

This migration plan transforms Surface Discovery from a deterministic pipeline into an intelligent agent framework while maintaining full backward compatibility. The phased approach ensures gradual, low-risk migration with clear success criteria at each stage.

**Key Success Factors:**
- Maintain existing pipeline mode indefinitely
- Agent mode achieves comparable or better results
- MCP integration enables broader ecosystem compatibility
- Cost controls prevent budget overruns
- Production-grade reliability and security

**Timeline:** 13 weeks to general availability (3.25 months)
**Risk Level:** Low to Medium (backward compatibility guaranteed)
**ROI:** High (autonomous operation, better adaptation, comprehensive discovery, learning)

**Ready to proceed with Phase 0: Deep URL Discovery Enhancement**
