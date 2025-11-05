"""Subprocess runner for external security tools"""
import asyncio
import shutil
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ToolNotFoundError(Exception):
    """Raised when required tool is not found in PATH"""
    pass


class ToolExecutionError(Exception):
    """Raised when tool execution fails"""
    pass


class ToolRunner:
    """Execute external security tools via subprocess"""

    def __init__(self, timeout: int = 300):
        """
        Args:
            timeout: Default timeout in seconds for tool execution
        """
        self.timeout = timeout
        self.required_tools = {
            'subfinder', 'httpx', 'nuclei', 'katana',
            'dnsx', 'naabu'
        }

    async def check_tool_installed(self, tool_name: str) -> bool:
        """Check if tool is installed and in PATH

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool is available
        """
        return shutil.which(tool_name) is not None

    async def check_dependencies(self) -> Dict[str, bool]:
        """Check all required tools are installed

        Returns:
            Dict mapping tool names to availability status
        """
        results = {}
        for tool in self.required_tools:
            results[tool] = await self.check_tool_installed(tool)

        missing = [tool for tool, available in results.items() if not available]
        if missing:
            logger.warning(f"Missing tools: {', '.join(missing)}")

        return results

    async def run(
        self,
        command: List[str],
        timeout: Optional[int] = None,
        check: bool = True
    ) -> tuple[str, str, int]:
        """Run external command asynchronously

        Args:
            command: Command and arguments as list
            timeout: Optional timeout override
            check: Raise error if command fails

        Returns:
            Tuple of (stdout, stderr, return_code)

        Raises:
            ToolNotFoundError: If tool not found in PATH
            ToolExecutionError: If command fails and check=True
            asyncio.TimeoutError: If command times out
        """
        tool_name = command[0]
        timeout = timeout or self.timeout

        # Check tool is available
        if not await self.check_tool_installed(tool_name):
            raise ToolNotFoundError(f"Tool not found: {tool_name}")

        logger.debug(f"Running: {' '.join(command)}")

        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            return_code = process.returncode

            # Log output
            if return_code != 0:
                logger.warning(
                    f"Tool {tool_name} exited with code {return_code}: {stderr_str[:200]}"
                )

            # Check for errors
            if check and return_code != 0:
                raise ToolExecutionError(
                    f"Tool {tool_name} failed: {stderr_str[:500]}"
                )

            return stdout_str, stderr_str, return_code

        except asyncio.TimeoutError:
            logger.error(f"Tool {tool_name} timed out after {timeout}s")
            try:
                process.kill()
                await process.wait()
            except:
                pass
            raise

        except Exception as e:
            logger.error(f"Tool {tool_name} execution error: {e}")
            raise ToolExecutionError(f"Failed to execute {tool_name}: {e}")

    async def run_subfinder(
        self,
        domain: str,
        timeout: Optional[int] = None,
        silent: bool = True
    ) -> str:
        """Run subfinder for subdomain enumeration

        Args:
            domain: Target domain
            timeout: Optional timeout override
            silent: Silent mode (less output)

        Returns:
            Raw stdout output
        """
        command = ['subfinder', '-d', domain]
        if silent:
            command.append('-silent')

        stdout, _, _ = await self.run(command, timeout=timeout, check=False)
        return stdout

    async def run_httpx(
        self,
        targets: List[str],
        timeout: Optional[int] = None,
        tech_detect: bool = True,
        follow_redirects: bool = True,
        json_output: bool = True
    ) -> str:
        """Run httpx for HTTP probing and tech detection

        Args:
            targets: List of domains/URLs to probe
            timeout: Optional timeout override
            tech_detect: Enable technology detection
            follow_redirects: Follow HTTP redirects
            json_output: Output in JSON format

        Returns:
            Raw stdout output
        """
        command = ['httpx', '-silent']

        if tech_detect:
            command.extend(['-tech-detect'])
        if follow_redirects:
            command.extend(['-follow-redirects'])
        if json_output:
            command.append('-json')

        # Write targets to temp file
        targets_input = '\n'.join(targets)

        # Run with piped input
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=targets_input.encode()),
            timeout=timeout or self.timeout
        )

        return stdout.decode('utf-8', errors='replace')

    async def run_dnsx(
        self,
        domains: List[str],
        record_types: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> str:
        """Run dnsx for DNS record retrieval

        Args:
            domains: List of domains to query
            record_types: DNS record types (A, AAAA, MX, TXT, etc.)
            timeout: Optional timeout override

        Returns:
            Raw stdout output
        """
        command = ['dnsx', '-silent', '-json']

        if record_types:
            for record_type in record_types:
                command.extend(['-' + record_type.lower()])
        else:
            # Default: A, AAAA records
            command.extend(['-a', '-aaaa'])

        # Write domains to pipe
        domains_input = '\n'.join(domains)

        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=domains_input.encode()),
            timeout=timeout or self.timeout
        )

        return stdout.decode('utf-8', errors='replace')

    async def run_nuclei(
        self,
        targets: List[str],
        templates: Optional[List[str]] = None,
        severity: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> str:
        """Run nuclei for template-based scanning

        Args:
            targets: List of URLs to scan
            templates: Specific template paths/tags
            severity: Severity levels to include (info, low, medium, high, critical)
            timeout: Optional timeout override

        Returns:
            Raw stdout output
        """
        command = ['nuclei', '-silent', '-json']

        if templates:
            for template in templates:
                command.extend(['-t', template])

        if severity:
            command.extend(['-severity', ','.join(severity)])

        # Write targets to pipe
        targets_input = '\n'.join(targets)

        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=targets_input.encode()),
            timeout=timeout or self.timeout
        )

        return stdout.decode('utf-8', errors='replace')

    async def run_katana(
        self,
        targets: List[str],
        depth: int = 2,
        js_crawl: bool = True,
        timeout: Optional[int] = None
    ) -> str:
        """Run katana for web crawling and endpoint discovery

        Args:
            targets: List of URLs to crawl
            depth: Crawl depth (default: 2)
            js_crawl: Enable JavaScript crawling (default: True)
            timeout: Optional timeout override

        Returns:
            Raw stdout output (JSONL format)
        """
        command = ['katana', '-silent', '-jsonl']

        # Set crawl depth
        command.extend(['-depth', str(depth)])

        # Enable JavaScript crawling
        if js_crawl:
            command.append('-jc')

        # Write targets to pipe
        targets_input = '\n'.join(targets)

        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=targets_input.encode()),
            timeout=timeout or self.timeout
        )

        return stdout.decode('utf-8', errors='replace')
