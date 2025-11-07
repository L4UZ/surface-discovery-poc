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
        logger.debug(f"[PORT_DISCOVERY] Initializing port discovery with config: {config}")
        self.config = config
        self.runner = ToolRunner(timeout=config.naabu_timeout if hasattr(config, 'naabu_timeout') else 180)

    async def run(self, subdomains: List[Subdomain]) -> PortDiscoveryResults:
        """Execute port discovery stage

        Args:
            subdomains: List of discovered subdomains to scan

        Returns:
            PortDiscoveryResults with scan statistics
        """
        logger.info(f"[PORT_DISCOVERY] Starting port discovery for {len(subdomains)} subdomains")
        logger.info(f"[PORT_DISCOVERY] Config depth: {self.config.depth}, naabu_timeout: {self.config.naabu_timeout}")
        results = PortDiscoveryResults()

        # Filter subdomains that have IP addresses
        scannable_subdomains = [sub for sub in subdomains if sub.ips]
        filtered_out = len(subdomains) - len(scannable_subdomains)

        logger.info(f"[PORT_DISCOVERY] Filtered: {filtered_out}, Scannable: {len(scannable_subdomains)}")

        if filtered_out > 0:
            logger.warning(
                f"Filtered out {filtered_out}/{len(subdomains)} subdomains with no resolved IPs"
            )

        if not scannable_subdomains:
            logger.warning(
                "No subdomains with resolved IPs to scan - skipping port discovery"
            )
            return results

        logger.info(f"Scanning {len(scannable_subdomains)} subdomains with resolved IPs")

        # Prepare hosts for scanning (use IPs for better reliability)
        hosts_to_scan = []
        subdomain_by_ip = {}  # Map IP back to subdomain for result association

        for subdomain in scannable_subdomains:
            for ip in subdomain.ips:
                hosts_to_scan.append(ip)
                subdomain_by_ip[ip] = subdomain

        logger.info(f"[PORT_DISCOVERY] Built hosts_to_scan list: {len(hosts_to_scan)} IPs from {len(scannable_subdomains)} subdomains")

        # Determine port configuration based on depth and host count
        ports, top_ports, rate = self._get_port_config(len(hosts_to_scan))
        logger.info(f"[PORT_DISCOVERY] Port config: ports={ports}, top_ports={top_ports}, rate={rate}")

        # Log progress estimate for deep scans
        if self.config.depth == "deep":
            estimated_time = self._estimate_scan_time(len(hosts_to_scan), ports, top_ports, rate)
            logger.info(
                f"Deep port scan starting: {len(hosts_to_scan)} hosts, "
                f"estimated time: {estimated_time:.1f} minutes"
            )

        try:
            # Run naabu port scan
            logger.info(f"[PORT_DISCOVERY] Calling naabu with {len(hosts_to_scan)} hosts, timeout={self.config.naabu_timeout if hasattr(self.config, 'naabu_timeout') else 180}s")
            output = await self.runner.run_naabu(
                hosts=hosts_to_scan,
                ports=ports,
                top_ports=top_ports,
                rate=rate,
                timeout=self.config.naabu_timeout if hasattr(self.config, 'naabu_timeout') else 180
            )
            logger.info(f"[PORT_DISCOVERY] naabu completed, parsing output...")

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

    def _get_port_config(self, host_count: int):
        """Get port configuration based on discovery depth and host count

        Adaptive configuration: For deep scans with many hosts, use top 10K ports
        instead of full range to stay within timeout limits while maintaining
        comprehensive coverage.

        Args:
            host_count: Number of hosts to scan

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
            # Adaptive configuration based on host count
            # For many hosts (>50), scanning all 65535 ports would exceed timeout
            # Math: 50 hosts × 65535 ports / 3000 pps = ~18 minutes
            # Instead use top 10K ports: 50 hosts × 10000 ports / 3000 pps = ~3 minutes
            if host_count > 50:
                logger.info(
                    f"Deep scan with {host_count} hosts: using top 10K ports "
                    f"instead of full range to stay within timeout"
                )
                return None, 10000, 3000  # Top 10K ports, higher rate
            else:
                # For fewer hosts, full port range is feasible
                logger.info(
                    f"Deep scan with {host_count} hosts: using full port range (65535)"
                )
                return "-", None, 3000  # Full range, increased rate from 2000→3000
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

    def _estimate_scan_time(
        self,
        host_count: int,
        ports: str,
        top_ports: int,
        rate: int
    ) -> float:
        """Estimate port scan time in minutes

        Args:
            host_count: Number of hosts to scan
            ports: Port specification ("-" for all)
            top_ports: Top N ports to scan
            rate: Packets per second

        Returns:
            Estimated time in minutes
        """
        # Calculate total port checks
        if top_ports:
            total_checks = host_count * top_ports
        elif ports == "-":
            total_checks = host_count * 65535
        else:
            total_checks = host_count * 1000  # Conservative estimate

        # Estimate time: total_checks / rate / 60 (convert to minutes)
        # Add 20% overhead for network latency and processing
        estimated_seconds = (total_checks / rate) * 1.2
        return estimated_seconds / 60
