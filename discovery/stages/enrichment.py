"""Enrichment stage - infrastructure and technology intelligence"""
import logging
import re
from typing import List, Dict, Optional, Set
from ipaddress import ip_address, ip_network
from pydantic import BaseModel, Field

from ..models import Service, Subdomain

logger = logging.getLogger(__name__)


class EnrichmentResults(BaseModel):
    """Results from enrichment stage"""
    cloud_providers: Dict[str, Set[str]] = Field(
        default_factory=dict,
        description="Cloud providers mapped to service URLs"
    )
    cdn_providers: Dict[str, Set[str]] = Field(
        default_factory=dict,
        description="CDN providers mapped to service URLs"
    )
    asn_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="IP to ASN mappings"
    )
    infrastructure_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Infrastructure statistics"
    )

    class Config:
        arbitrary_types_allowed = True


class EnrichmentStage:
    """Enrichment stage - infrastructure and technology detection"""

    # Cloud provider IP ranges (simplified - in production, use official IP lists)
    CLOUD_PROVIDERS = {
        'AWS': [
            ip_network('3.0.0.0/8'),
            ip_network('13.0.0.0/8'),
            ip_network('18.0.0.0/8'),
            ip_network('52.0.0.0/8'),
            ip_network('54.0.0.0/8'),
        ],
        'GCP': [
            ip_network('34.64.0.0/10'),
            ip_network('35.184.0.0/13'),
        ],
        'Azure': [
            ip_network('13.64.0.0/11'),
            ip_network('20.0.0.0/8'),
            ip_network('40.64.0.0/10'),
        ],
        'Cloudflare': [
            ip_network('104.16.0.0/12'),
            ip_network('172.64.0.0/13'),
            ip_network('173.245.48.0/20'),
        ],
        'DigitalOcean': [
            ip_network('104.131.0.0/16'),
            ip_network('159.65.0.0/16'),
            ip_network('167.99.0.0/16'),
        ],
    }

    # CDN detection patterns
    CDN_PATTERNS = {
        'Cloudflare': [
            r'cloudflare',
            r'cf-ray',
            r'__cfduid',
        ],
        'Akamai': [
            r'akamai',
            r'akamaihd',
        ],
        'Fastly': [
            r'fastly',
            r'x-fastly',
        ],
        'CloudFront': [
            r'cloudfront',
            r'x-amz-cf',
        ],
        'MaxCDN': [
            r'maxcdn',
        ],
    }

    def __init__(self):
        """Initialize enrichment stage"""
        pass

    async def run(
        self,
        services: List[Service],
        subdomains: List[Subdomain]
    ) -> EnrichmentResults:
        """Execute enrichment stage

        Args:
            services: List of discovered services
            subdomains: List of discovered subdomains

        Returns:
            EnrichmentResults with infrastructure intelligence
        """
        logger.info(f"Starting enrichment for {len(services)} services, {len(subdomains)} subdomains")
        results = EnrichmentResults()

        # Collect all IPs from subdomains
        all_ips = set()
        for subdomain in subdomains:
            all_ips.update(subdomain.ips)

        # Phase 1: Cloud provider detection from IPs
        cloud_mappings = self._detect_cloud_providers(all_ips, subdomains)
        results.cloud_providers = cloud_mappings

        # Phase 2: CDN detection from services
        cdn_mappings = self._detect_cdn_providers(services)
        results.cdn_providers = cdn_mappings

        # Phase 3: Generate infrastructure summary
        results.infrastructure_summary = {
            'total_cloud_ips': sum(len(ips) for ips in cloud_mappings.values()),
            'total_cdn_services': sum(len(services) for services in cdn_mappings.values()),
            'cloud_providers_count': len(cloud_mappings),
            'cdn_providers_count': len(cdn_mappings),
        }

        logger.info(f"Enrichment complete: {len(cloud_mappings)} cloud providers, "
                   f"{len(cdn_mappings)} CDN providers detected")

        return results

    def _detect_cloud_providers(
        self,
        ips: Set[str],
        subdomains: List[Subdomain]
    ) -> Dict[str, Set[str]]:
        """Detect cloud providers from IP addresses

        Args:
            ips: Set of IP addresses
            subdomains: List of subdomains with IPs

        Returns:
            Dict mapping cloud provider names to subdomain names
        """
        cloud_mappings = {}

        # Build IP to subdomain mapping
        ip_to_subdomains = {}
        for subdomain in subdomains:
            for ip in subdomain.ips:
                if ip not in ip_to_subdomains:
                    ip_to_subdomains[ip] = set()
                ip_to_subdomains[ip].add(subdomain.name)

        # Check each IP against cloud provider ranges
        for ip_str in ips:
            try:
                ip_obj = ip_address(ip_str)

                # Skip private IPs
                if ip_obj.is_private:
                    continue

                # Check against each cloud provider
                for provider, ranges in self.CLOUD_PROVIDERS.items():
                    for network in ranges:
                        if ip_obj in network:
                            if provider not in cloud_mappings:
                                cloud_mappings[provider] = set()

                            # Add all subdomains using this IP
                            if ip_str in ip_to_subdomains:
                                cloud_mappings[provider].update(ip_to_subdomains[ip_str])
                            break

            except ValueError:
                # Invalid IP address, skip
                logger.debug(f"Invalid IP address: {ip_str}")
                continue

        return cloud_mappings

    def _detect_cdn_providers(self, services: List[Service]) -> Dict[str, Set[str]]:
        """Detect CDN providers from service responses

        Args:
            services: List of discovered services

        Returns:
            Dict mapping CDN provider names to service URLs
        """
        cdn_mappings = {}

        for service in services:
            # Check server header
            server = service.server or ''

            # Check technologies
            tech_names = [tech.name.lower() for tech in service.technologies]

            # Combine all searchable text
            searchable = f"{server.lower()} {' '.join(tech_names)}"

            # Check against CDN patterns
            for cdn_name, patterns in self.CDN_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, searchable, re.IGNORECASE):
                        if cdn_name not in cdn_mappings:
                            cdn_mappings[cdn_name] = set()
                        cdn_mappings[cdn_name].add(service.url)
                        break  # Found match for this CDN

        return cdn_mappings
