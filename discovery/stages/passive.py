"""Passive discovery stage - reconnaissance without active probing"""
import asyncio
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field

from ..tools.runner import ToolRunner
from ..tools.parsers import SubfinderParser, DNSXParser, parse_subdomain_list
from ..models import Subdomain, DNSRecords, DomainInfo, WHOISData
from ..config import DiscoveryConfig

logger = logging.getLogger(__name__)


class PassiveResults(BaseModel):
    """Results from passive discovery stage"""
    subdomains: List[str] = Field(default_factory=list, description="Discovered subdomains")
    dns_records: Dict[str, DNSRecords] = Field(
        default_factory=dict,
        description="DNS records mapped by hostname"
    )
    whois_data: Optional[WHOISData] = None
    total_subdomains: int = 0
    unique_ips: Set[str] = Field(default_factory=set)

    class Config:
        arbitrary_types_allowed = True  # Allow Set type


class PassiveDiscovery:
    """Passive reconnaissance stage"""

    def __init__(self, config: DiscoveryConfig):
        """
        Args:
            config: Discovery configuration
        """
        self.config = config
        self.runner = ToolRunner(timeout=config.subfinder_timeout)

    async def run(self, target_domain: str) -> PassiveResults:
        """Execute passive discovery stage

        Args:
            target_domain: Root domain to discover

        Returns:
            PassiveResults with discovered data
        """
        logger.info(f"Starting passive discovery for {target_domain}")
        results = PassiveResults()

        # Phase 1: Run subdomain enumeration and WHOIS in parallel
        subdomain_task = self._enumerate_subdomains(target_domain)
        whois_task = self._fetch_whois(target_domain)

        subdomain_results, whois_result = await asyncio.gather(
            subdomain_task,
            whois_task,
            return_exceptions=True
        )

        # Process subdomain enumeration results
        if isinstance(subdomain_results, Exception):
            logger.error(f"Subdomain enumeration failed: {subdomain_results}")
            results.subdomains = []
        else:
            results.subdomains = subdomain_results
            results.total_subdomains = len(subdomain_results)
            logger.info(f"Discovered {results.total_subdomains} subdomains")

        # Process WHOIS results
        if isinstance(whois_result, Exception):
            logger.warning(f"WHOIS lookup failed: {whois_result}")
        else:
            results.whois_data = whois_result

        # Phase 2: Collect DNS records for root domain AND all discovered subdomains
        try:
            dns_results = await self._collect_dns_records(target_domain, results.subdomains)
            results.dns_records = dns_results

            # Extract unique IPs
            for dns_data in dns_results.values():
                if dns_data.a:
                    results.unique_ips.update(dns_data.a)
                if dns_data.aaaa:
                    results.unique_ips.update(dns_data.aaaa)

            logger.info(f"Collected DNS records for {len(dns_results)} hosts, "
                       f"{len(results.unique_ips)} unique IPs")
        except Exception as e:
            logger.error(f"DNS collection failed: {e}")
            results.dns_records = {}

        logger.info(f"Passive discovery complete: {results.total_subdomains} subdomains, "
                   f"{len(results.unique_ips)} unique IPs")

        return results

    async def _enumerate_subdomains(self, domain: str) -> List[str]:
        """Enumerate subdomains using multiple sources

        Args:
            domain: Target domain

        Returns:
            List of discovered subdomains
        """
        logger.debug(f"Enumerating subdomains for {domain}")
        all_subdomains = set()

        # Run subfinder
        try:
            output = await self.runner.run_subfinder(
                domain,
                timeout=self.config.subfinder_timeout,
                silent=True
            )
            subdomains = SubfinderParser.parse(output)
            all_subdomains.update(subdomains)
            logger.debug(f"Subfinder found {len(subdomains)} subdomains")

        except Exception as e:
            logger.error(f"Subfinder execution failed: {e}")

        # Apply limit if configured
        if self.config.max_subdomains:
            all_subdomains = set(list(all_subdomains)[:self.config.max_subdomains])
            logger.debug(f"Limited to {self.config.max_subdomains} subdomains")

        return sorted(list(all_subdomains))

    async def _collect_dns_records(self, domain: str, subdomains: List[str] = None) -> Dict[str, DNSRecords]:
        """Collect DNS records for domain and subdomains

        Args:
            domain: Target root domain
            subdomains: List of discovered subdomains to resolve

        Returns:
            Dict mapping hostnames to DNS records
        """
        logger.debug(f"Collecting DNS records for {domain} and {len(subdomains or [])} subdomains")
        dns_data = {}

        try:
            # Always get full records for root domain
            logger.debug(f"Querying full DNS records for root domain: {domain}")
            root_output = await self.runner.run_dnsx(
                domains=[domain],
                record_types=['A', 'AAAA', 'MX', 'TXT', 'NS'],
                timeout=self.config.dnsx_timeout
            )
            root_dns_data = DNSXParser.parse(root_output)
            dns_data.update(root_dns_data)

            # Resolve subdomains if present (A and AAAA records only for efficiency)
            if subdomains:
                logger.info(f"Resolving {len(subdomains)} subdomains to IP addresses...")
                subdomain_output = await self.runner.run_dnsx(
                    domains=subdomains,
                    record_types=['A', 'AAAA'],
                    timeout=self.config.dnsx_timeout
                )
                subdomain_dns_data = DNSXParser.parse(subdomain_output)
                dns_data.update(subdomain_dns_data)
                logger.info(f"DNS resolution complete: {len(subdomain_dns_data)}/{len(subdomains)} subdomains returned records")

            logger.debug(f"Collected DNS records for {len(dns_data)} hosts")

        except Exception as e:
            logger.error(f"DNS collection failed: {e}")
            raise

        return dns_data

    async def _fetch_whois(self, domain: str) -> Optional[WHOISData]:
        """Fetch WHOIS data for domain

        Args:
            domain: Target domain

        Returns:
            WHOISData if successful, None otherwise
        """
        logger.debug(f"Fetching WHOIS data for {domain}")

        try:
            import whois

            # Perform WHOIS lookup (blocking call, but quick)
            w = await asyncio.to_thread(whois.whois, domain)

            # Parse WHOIS response
            whois_data = WHOISData(
                registrar=w.registrar if hasattr(w, 'registrar') else None,
                creation_date=self._parse_whois_date(w.creation_date) if hasattr(w, 'creation_date') else None,
                expiration_date=self._parse_whois_date(w.expiration_date) if hasattr(w, 'expiration_date') else None,
                name_servers=self._parse_whois_list(w.name_servers) if hasattr(w, 'name_servers') else [],
                status=self._parse_whois_list(w.status) if hasattr(w, 'status') else [],
                emails=self._parse_whois_list(w.emails) if hasattr(w, 'emails') else []
            )

            logger.debug(f"WHOIS data retrieved for {domain}")
            return whois_data

        except ImportError:
            logger.warning("python-whois not installed, skipping WHOIS lookup")
            return None
        except Exception as e:
            logger.warning(f"WHOIS lookup failed: {e}")
            return None

    def _parse_whois_date(self, date_value) -> Optional[datetime]:
        """Parse WHOIS date field (can be datetime, list, or str)

        Args:
            date_value: WHOIS date value

        Returns:
            Parsed datetime or None
        """
        if isinstance(date_value, datetime):
            return date_value
        elif isinstance(date_value, list) and len(date_value) > 0:
            if isinstance(date_value[0], datetime):
                return date_value[0]
        return None

    def _parse_whois_list(self, value) -> List[str]:
        """Parse WHOIS list field (can be list, str, or None)

        Args:
            value: WHOIS field value

        Returns:
            List of strings
        """
        if value is None:
            return []
        elif isinstance(value, list):
            return [str(item) for item in value if item]
        elif isinstance(value, str):
            return [value] if value else []
        else:
            return []

    def to_domain_info(self, target: str, results: PassiveResults) -> DomainInfo:
        """Convert PassiveResults to DomainInfo model

        Args:
            target: Root domain
            results: Passive discovery results

        Returns:
            DomainInfo object
        """
        # Convert subdomains to Subdomain objects
        subdomain_objects = []
        resolved_count = 0

        for subdomain_name in results.subdomains:
            # Get DNS records if available
            dns_records = results.dns_records.get(subdomain_name)

            # Extract IPs from DNS
            ips = []
            if dns_records:
                ips.extend(dns_records.a)
                ips.extend(dns_records.aaaa)
                if ips:
                    resolved_count += 1

            subdomain = Subdomain(
                name=subdomain_name,
                ips=ips,
                status="unknown",  # Will be determined in active discovery
                dns_records=dns_records,
                discovered_via="passive",
                discovered_at=datetime.utcnow()
            )
            subdomain_objects.append(subdomain)

        # Log IP resolution statistics
        logger.info(
            f"DNS resolution: {resolved_count}/{len(subdomain_objects)} subdomains resolved to IPs"
        )
        if resolved_count == 0:
            logger.warning(
                "No subdomains resolved to IP addresses - port scanning and active discovery will be skipped"
            )

        # Build DomainInfo
        domain_info = DomainInfo(
            root_domain=target,
            subdomains=subdomain_objects,
            dns_records=results.dns_records.get(target),
            whois=results.whois_data,
            total_subdomains=len(subdomain_objects),
            live_subdomains=0  # Will be updated in active discovery
        )

        return domain_info
