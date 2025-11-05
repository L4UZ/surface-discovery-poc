"""Port discovery stage - network-level port scanning"""
import asyncio
import logging
import json
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from ..tools.runner import ToolRunner
from ..models import Subdomain, PortScanResult
from ..config import DiscoveryConfig

logger = logging.getLogger(__name__)


class PortDiscoveryResults(BaseModel):
    """Results from port discovery stage"""
    total_hosts_scanned: int = 0
    total_ports_scanned: int = 0
    total_open_ports: int = 0
    ports_by_host: Dict[str, int] = Field(default_factory=dict, description="Open ports count per host")


class PortDiscovery:
    """Port scanning stage using naabu"""

    def __init__(self, config: DiscoveryConfig):
        """
        Args:
            config: Discovery configuration
        """
        self.config = config
        self.runner = ToolRunner(timeout=config.naabu_timeout if hasattr(config, 'naabu_timeout') else 180)

    async def run(self, subdomains: List[Subdomain]) -> PortDiscoveryResults:
        """Execute port discovery stage

        Args:
            subdomains: List of discovered subdomains to scan

        Returns:
            PortDiscoveryResults with scan statistics
        """
        logger.info(f"Starting port discovery for {len(subdomains)} subdomains")
        results = PortDiscoveryResults()

        # Filter subdomains that have IP addresses
        scannable_subdomains = [sub for sub in subdomains if sub.ips]

        if not scannable_subdomains:
            logger.warning("No subdomains with resolved IPs to scan")
            return results

        logger.info(f"Scanning {len(scannable_subdomains)} subdomains with resolved IPs")

        # Prepare hosts for scanning (use IPs for better reliability)
        hosts_to_scan = []
        subdomain_by_ip = {}  # Map IP back to subdomain for result association

        for subdomain in scannable_subdomains:
            for ip in subdomain.ips:
                hosts_to_scan.append(ip)
                subdomain_by_ip[ip] = subdomain

        # Determine port configuration based on depth
        ports, top_ports, rate = self._get_port_config()

        try:
            # Run naabu port scan
            output = await self.runner.run_naabu(
                hosts=hosts_to_scan,
                ports=ports,
                top_ports=top_ports,
                rate=rate,
                timeout=self.config.naabu_timeout if hasattr(self.config, 'naabu_timeout') else 180
            )

            # Parse results
            results.total_hosts_scanned = len(hosts_to_scan)
            port_results = self._parse_naabu_output(output, subdomain_by_ip)

            # Update subdomain objects with port scan results
            for subdomain in scannable_subdomains:
                if subdomain.open_ports:
                    subdomain.open_ports_count = len(subdomain.open_ports)
                    results.total_open_ports += len(subdomain.open_ports)
                    results.ports_by_host[subdomain.name] = len(subdomain.open_ports)

            # Calculate total ports scanned
            if top_ports:
                results.total_ports_scanned = len(hosts_to_scan) * top_ports
            elif ports == "-":
                results.total_ports_scanned = len(hosts_to_scan) * 65535
            else:
                # Estimate based on port specification
                results.total_ports_scanned = len(hosts_to_scan) * 100  # Conservative estimate

            logger.info(
                f"Port discovery complete: {results.total_open_ports} open ports found "
                f"across {len(results.ports_by_host)} hosts"
            )

        except Exception as e:
            logger.error(f"Port discovery failed: {e}")
            raise

        return results

    def _get_port_config(self):
        """Get port configuration based on discovery depth

        Returns:
            Tuple of (ports, top_ports, rate)
        """
        depth = self.config.depth

        if depth == "shallow":
            # Top 100 ports, conservative rate
            return None, 100, 1000
        elif depth == "normal":
            # Top 1000 ports, moderate rate
            return None, 1000, 1500
        elif depth == "deep":
            # Full port range, aggressive rate
            return "-", None, 2000
        else:
            # Fallback to normal
            return None, 1000, 1500

    def _parse_naabu_output(
        self,
        output: str,
        subdomain_by_ip: Dict[str, Subdomain]
    ) -> int:
        """Parse naabu JSON output and update subdomain objects

        Args:
            output: Raw naabu output (JSON lines)
            subdomain_by_ip: Mapping of IP to Subdomain object

        Returns:
            Count of open ports found
        """
        if not output or not output.strip():
            logger.debug("Naabu returned no output (no open ports found)")
            return 0

        port_count = 0

        for line in output.strip().split('\n'):
            if not line or not line.strip():
                continue

            try:
                data = json.loads(line)
                ip = data.get('ip')
                port = data.get('port')

                if not ip or not port:
                    continue

                # Find associated subdomain
                subdomain = subdomain_by_ip.get(ip)
                if not subdomain:
                    logger.debug(f"No subdomain found for IP {ip}, skipping")
                    continue

                # Create PortScanResult
                port_result = PortScanResult(
                    port=port,
                    protocol="tcp",  # naabu default is TCP
                    state="open",    # naabu only reports open ports
                    service=None,    # naabu doesn't detect service names by default
                    version=None,
                    discovered_at=datetime.utcnow()
                )

                # Add to subdomain's port list
                subdomain.open_ports.append(port_result)
                subdomain.total_ports_scanned = self._estimate_ports_scanned()
                port_count += 1

                logger.debug(f"Found open port {port} on {subdomain.name} ({ip})")

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse naabu JSON line: {e}")
                logger.debug(f"Problematic line: {line[:100]}")
                continue
            except Exception as e:
                logger.warning(f"Error processing port result: {e}")
                continue

        return port_count

    def _estimate_ports_scanned(self) -> int:
        """Estimate number of ports scanned based on depth"""
        depth = self.config.depth

        if depth == "shallow":
            return 100
        elif depth == "normal":
            return 1000
        elif depth == "deep":
            return 65535
        else:
            return 1000
