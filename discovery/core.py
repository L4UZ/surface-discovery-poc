"""Core orchestration engine for discovery pipeline"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

from .config import DiscoveryConfig, get_config
from .models import DiscoveryResult, DiscoveryMetadata, DiscoveryStage
from .stages.passive import PassiveDiscovery
from .stages.active import ActiveDiscovery
from .utils.helpers import extract_domain
from .utils.logger import setup_logger

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Main orchestration engine for attack surface discovery"""

    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """
        Args:
            config: Discovery configuration (uses default if not provided)
        """
        self.config = config or get_config()
        self.result: Optional[DiscoveryResult] = None

    async def discover(self, target_url: str) -> DiscoveryResult:
        """Execute full discovery pipeline

        Args:
            target_url: Target URL or domain

        Returns:
            DiscoveryResult with all discovered data

        Raises:
            ValueError: If target URL is invalid
        """
        # Setup logging
        global logger
        logger = setup_logger(__name__, verbose=self.config.verbose)

        # Extract and validate domain
        try:
            target_domain = extract_domain(target_url)
        except ValueError as e:
            raise ValueError(f"Invalid target URL: {e}")

        logger.info(f"Starting discovery for {target_domain} (depth: {self.config.depth})")

        # Initialize result
        scan_id = str(uuid.uuid4())
        metadata = DiscoveryMetadata(
            target=target_domain,
            scan_id=scan_id,
            start_time=datetime.utcnow(),
            discovery_depth=self.config.depth,
            status=DiscoveryStage.INITIALIZED
        )

        self.result = DiscoveryResult(metadata=metadata)
        self.result.add_timeline_event(
            DiscoveryStage.INITIALIZED,
            "Discovery initialized",
            {"target": target_domain, "config": self.config.depth}
        )

        try:
            # Stage 1: Passive Discovery
            await self._run_passive_discovery(target_domain)

            # Stage 2: Active Discovery (placeholder for core components)
            await self._run_active_discovery()

            # Finalize
            await self._finalize()

        except Exception as e:
            logger.error(f"Discovery failed: {e}", exc_info=True)
            self.result.metadata.status = DiscoveryStage.FAILED
            self.result.metadata.error = str(e)
            raise

        return self.result

    async def _run_passive_discovery(self, target_domain: str):
        """Execute passive discovery stage

        Args:
            target_domain: Target domain to discover
        """
        logger.info("Stage 1: Passive Discovery")
        self.result.metadata.status = DiscoveryStage.PASSIVE_DISCOVERY
        self.result.add_timeline_event(
            DiscoveryStage.PASSIVE_DISCOVERY,
            "Starting passive reconnaissance"
        )

        try:
            # Create passive discovery stage
            passive = PassiveDiscovery(self.config)

            # Run passive discovery
            passive_results = await passive.run(target_domain)

            # Convert to DomainInfo
            domain_info = passive.to_domain_info(target_domain, passive_results)

            # Store in result
            self.result.domains = domain_info

            self.result.add_timeline_event(
                DiscoveryStage.PASSIVE_DISCOVERY,
                "Passive discovery completed",
                {
                    "subdomains_found": len(passive_results.subdomains),
                    "unique_ips": len(passive_results.unique_ips)
                }
            )

            logger.info(f"Passive discovery complete: {len(passive_results.subdomains)} subdomains")

        except Exception as e:
            logger.error(f"Passive discovery failed: {e}")
            self.result.add_timeline_event(
                DiscoveryStage.PASSIVE_DISCOVERY,
                f"Passive discovery failed: {e}"
            )
            raise

    async def _run_active_discovery(self):
        """Execute active discovery stage

        Probes discovered subdomains for live HTTP/HTTPS services
        """
        logger.info("Stage 2: Active Discovery")
        self.result.metadata.status = DiscoveryStage.ACTIVE_DISCOVERY
        self.result.add_timeline_event(
            DiscoveryStage.ACTIVE_DISCOVERY,
            "Starting active probing"
        )

        try:
            # Get subdomains from passive discovery
            if not self.result.domains or not self.result.domains.subdomains:
                logger.warning("No subdomains found in passive discovery, skipping active stage")
                return

            # Extract subdomain names
            subdomain_names = [sub.name for sub in self.result.domains.subdomains]

            # Create active discovery stage
            active = ActiveDiscovery(self.config)

            # Run HTTP probing
            active_results = await active.run(subdomain_names)

            # Store services in result
            self.result.services = active_results.services

            # Update subdomain status based on probing results
            service_urls = {service.url for service in active_results.services}
            for subdomain in self.result.domains.subdomains:
                # Check if subdomain has any live service
                subdomain_live = any(
                    subdomain.name in url for url in service_urls
                )
                subdomain.status = "live" if subdomain_live else "dead"

            # Update live subdomain count
            self.result.domains.live_subdomains = sum(
                1 for sub in self.result.domains.subdomains if sub.status == "live"
            )

            # Extract all technologies from services
            all_technologies = []
            for service in active_results.services:
                all_technologies.extend(service.technologies)
            self.result.technologies = all_technologies

            self.result.add_timeline_event(
                DiscoveryStage.ACTIVE_DISCOVERY,
                "Active discovery completed",
                {
                    "live_services": active_results.live_count,
                    "dead_hosts": active_results.dead_count,
                    "technologies": len(all_technologies)
                }
            )

            logger.info(f"Active discovery complete: {active_results.live_count} live services")

        except Exception as e:
            logger.error(f"Active discovery failed: {e}")
            self.result.add_timeline_event(
                DiscoveryStage.ACTIVE_DISCOVERY,
                f"Active discovery failed: {e}"
            )
            raise

    async def _finalize(self):
        """Finalize discovery and update metadata"""
        logger.info("Finalizing discovery results")

        # Update statistics
        self.result.update_statistics()

        # Update metadata
        self.result.metadata.end_time = datetime.utcnow()
        duration = (self.result.metadata.end_time - self.result.metadata.start_time).total_seconds()
        self.result.metadata.duration_seconds = duration
        self.result.metadata.status = DiscoveryStage.COMPLETED

        self.result.add_timeline_event(
            DiscoveryStage.COMPLETED,
            "Discovery completed successfully",
            {"duration_seconds": duration}
        )

        logger.info(f"Discovery complete in {duration:.2f}s")


async def run_discovery(
    target: str,
    depth: str = "normal",
    **config_overrides
) -> DiscoveryResult:
    """Convenience function to run discovery

    Args:
        target: Target URL or domain
        depth: Discovery depth (shallow|normal|deep)
        **config_overrides: Additional configuration overrides

    Returns:
        DiscoveryResult
    """
    config = get_config(depth, **config_overrides)
    engine = DiscoveryEngine(config)
    return await engine.discover(target)
