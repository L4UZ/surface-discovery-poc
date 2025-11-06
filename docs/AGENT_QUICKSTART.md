# Agent Framework Quick Start Guide

**Get started with Phase 1 implementation in 30 minutes**

## Prerequisites

```bash
# Install dependencies
pip install langgraph langchain langchain-anthropic anthropic pydantic jsonschema

# Set API key
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

## Step 1: Create Project Structure (5 minutes)

```bash
# Create directories
mkdir -p discovery/agent/tools
mkdir -p discovery/agent/schemas
mkdir -p discovery/agent/prompts
mkdir -p discovery/engines
mkdir -p tests/agent

# Create __init__ files
touch discovery/agent/__init__.py
touch discovery/agent/tools/__init__.py
touch discovery/engines/__init__.py
```

## Step 2: Define First Tool Schema (10 minutes)

Create `discovery/agent/schemas/subfinder.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SubfinderTool",
  "description": "Enumerate subdomains using passive reconnaissance sources",
  "type": "object",
  "properties": {
    "domain": {
      "type": "string",
      "description": "Target domain to enumerate subdomains for",
      "pattern": "^[a-z0-9.-]+$",
      "examples": ["example.com", "test.org"]
    },
    "sources": {
      "type": "array",
      "description": "Specific sources to use (optional, uses all if not specified)",
      "items": {
        "type": "string",
        "enum": ["cert transparency", "virustotal", "threatcrowd", "hackertarget"]
      }
    },
    "timeout": {
      "type": "integer",
      "description": "Maximum execution time in seconds",
      "default": 180,
      "minimum": 30,
      "maximum": 600
    }
  },
  "required": ["domain"],
  "additionalProperties": false
}
```

## Step 3: Create Base Tool Class (10 minutes)

Create `discovery/agent/tools/base.py`:

```python
"""Base class for all reconnaissance tools"""
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator
from pydantic import BaseModel
import json
from pathlib import Path


class ToolResult(BaseModel):
    """Standardized tool execution result"""
    success: bool
    data: Dict[str, Any]
    error: str | None = None
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """Base class for reconnaissance tools"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict:
        """Load JSON schema for this tool"""
        schema_file = Path(__file__).parent.parent / "schemas" / f"{self.name.lower().replace('tool', '')}.json"
        if schema_file.exists():
            with open(schema_file) as f:
                return json.load(f)
        return {}

    @abstractmethod
    async def execute(self, **params) -> ToolResult:
        """Execute the tool with given parameters"""
        pass

    async def execute_streaming(self, **params) -> AsyncIterator[Dict]:
        """Execute with progress streaming (optional)"""
        result = await self.execute(**params)
        yield {"type": "result", "data": result.dict()}

    def validate_params(self, params: Dict) -> bool:
        """Validate parameters against schema"""
        # Use jsonschema for validation
        import jsonschema
        try:
            jsonschema.validate(params, self.schema)
            return True
        except jsonschema.ValidationError:
            return False
```

## Step 4: Implement First Tool Wrapper (15 minutes)

Create `discovery/agent/tools/subfinder.py`:

```python
"""Subfinder tool wrapper for agent use"""
from typing import Dict, Any
from .base import BaseTool, ToolResult
from ...tools.runner import ToolRunner


class SubfinderTool(BaseTool):
    """Subdomain enumeration using subfinder"""

    def __init__(self):
        super().__init__()
        self.runner = ToolRunner(timeout=300)
        self.description = "Enumerate subdomains using passive reconnaissance sources"

    async def execute(self, domain: str, sources: list[str] | None = None, timeout: int = 180) -> ToolResult:
        """
        Execute subfinder for subdomain enumeration

        Args:
            domain: Target domain
            sources: Optional list of specific sources to use
            timeout: Maximum execution time in seconds

        Returns:
            ToolResult with discovered subdomains
        """
        try:
            # Validate inputs
            if not self.validate_params({"domain": domain, "timeout": timeout}):
                return ToolResult(
                    success=False,
                    data={},
                    error="Invalid parameters"
                )

            # Execute subfinder
            output = await self.runner.run_subfinder(
                domain=domain,
                timeout=timeout,
                silent=True
            )

            # Parse results
            subdomains = [
                line.strip()
                for line in output.strip().split('\n')
                if line.strip()
            ]

            return ToolResult(
                success=True,
                data={
                    "domain": domain,
                    "subdomains": subdomains,
                    "count": len(subdomains)
                },
                metadata={
                    "tool": "subfinder",
                    "timeout": timeout
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e)
            )


# Export for easy import
__all__ = ["SubfinderTool"]
```

## Step 5: Create Tool Registry (10 minutes)

Create `discovery/agent/registry.py`:

```python
"""Central registry for all reconnaissance tools"""
from typing import Dict, List
from .tools.base import BaseTool
from .tools.subfinder import SubfinderTool


class ToolRegistry:
    """Registry for discovering and accessing reconnaissance tools"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register built-in reconnaissance tools"""
        self.register("subfinder_enumerate", SubfinderTool())
        # Add more tools as they're implemented:
        # self.register("naabu_scan", NaabuTool())
        # self.register("httpx_probe", HttpxTool())
        # etc.

    def register(self, name: str, tool: BaseTool):
        """Register a tool by name"""
        self.tools[name] = tool

    def get_tool(self, name: str) -> BaseTool | None:
        """Get tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict]:
        """List all registered tools with metadata"""
        return [
            {
                "name": name,
                "description": tool.description,
                "schema": tool.schema
            }
            for name, tool in self.tools.items()
        ]

    def get_tool_names(self) -> List[str]:
        """Get list of registered tool names"""
        return list(self.tools.keys())


# Global registry instance
_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get global tool registry"""
    return _registry
```

## Step 6: Write First Test (10 minutes)

Create `tests/agent/test_subfinder_tool.py`:

```python
"""Tests for Subfinder tool wrapper"""
import pytest
from discovery.agent.tools.subfinder import SubfinderTool


@pytest.mark.asyncio
async def test_subfinder_tool_basic():
    """Test basic subfinder execution"""
    tool = SubfinderTool()

    result = await tool.execute(domain="example.com", timeout=60)

    assert result.success is True
    assert "subdomains" in result.data
    assert isinstance(result.data["subdomains"], list)
    assert result.data["domain"] == "example.com"


@pytest.mark.asyncio
async def test_subfinder_tool_invalid_domain():
    """Test subfinder with invalid domain"""
    tool = SubfinderTool()

    result = await tool.execute(domain="", timeout=60)

    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_subfinder_tool_validation():
    """Test parameter validation"""
    tool = SubfinderTool()

    # Valid params
    assert tool.validate_params({"domain": "example.com", "timeout": 180}) is True

    # Invalid timeout
    assert tool.validate_params({"domain": "example.com", "timeout": 10}) is False

    # Missing required field
    assert tool.validate_params({"timeout": 180}) is False
```

## Step 7: Test Your Implementation (5 minutes)

```bash
# Run tests
pytest tests/agent/test_subfinder_tool.py -v

# Test tool registry
python -c "
from discovery.agent.registry import get_registry

registry = get_registry()
print('Registered tools:', registry.get_tool_names())

tools = registry.list_tools()
for tool in tools:
    print(f\"Tool: {tool['name']}\")
    print(f\"Description: {tool['description']}\")
"

# Test tool execution
python -c "
import asyncio
from discovery.agent.tools.subfinder import SubfinderTool

async def main():
    tool = SubfinderTool()
    result = await tool.execute(domain='example.com', timeout=60)
    print(f'Success: {result.success}')
    print(f'Subdomains found: {result.data.get(\"count\", 0)}')

asyncio.run(main())
"
```

## Next Steps

### Implement More Tools

Following the same pattern, implement:

1. **NaabuTool** (`discovery/agent/tools/naabu.py`)
   - Schema: `discovery/agent/schemas/naabu.json`
   - Wraps: `ToolRunner.run_naabu()`

2. **HttpxTool** (`discovery/agent/tools/httpx.py`)
   - Schema: `discovery/agent/schemas/httpx.json`
   - Wraps: `ToolRunner.run_httpx()`

3. **KatanaTool** (`discovery/agent/tools/katana.py`)
   - Schema: `discovery/agent/schemas/katana.json`
   - Wraps: `ToolRunner.run_katana()`

### Move to Phase 2: Agent Core

Once you have 3-4 tools implemented, proceed to:
- LangGraph setup
- ReAct loop implementation
- Prompt engineering

See [AGENT_MIGRATION_PLAN.md](AGENT_MIGRATION_PLAN.md) for complete roadmap.

## Troubleshooting

### jsonschema not found
```bash
pip install jsonschema
```

### ToolRunner import error
```bash
# Ensure you're in the project root
cd /path/to/surface-discovery
# Install in development mode
pip install -e .
```

### Tests fail with import errors
```bash
# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/agent/
```

## Resources

- [Full Migration Plan](AGENT_MIGRATION_PLAN.md)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [MCP Protocol Spec](https://modelcontextprotocol.io)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)

---

**Estimated Time:** 60 minutes to complete all steps
**Next:** Implement remaining tools (naabu, httpx, katana) following the same pattern
