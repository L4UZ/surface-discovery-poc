"""Active discovery stage - HTTP probing and service detection"""
import asyncio
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ..tools.runner import ToolRunner
from ..models import Service, Technology, SecurityHeaders, TLSInfo
from ..config import DiscoveryConfig

logger = logging.getLogger(__name__)


class ActiveResults(BaseModel):
    """Results from active discovery stage"""
    services: List[Service] = Field(default_factory=list, description="Discovered live services")
    live_count: int = 0
    dead_count: int = 0
    total_probed: int = 0

    class Config:
        arbitrary_types_allowed = True


class ActiveDiscovery:
    """Active reconnaissance stage - HTTP probing and service detection"""

    def __init__(self, config: DiscoveryConfig):
        """
        Args:
            config: Discovery configuration
        """
        self.config = config
        self.runner = ToolRunner(timeout=config.httpx_timeout)

    async def run(self, subdomains: List[str]) -> ActiveResults:
        """Execute active discovery stage

        Args:
            subdomains: List of subdomains to probe

        Returns:
            ActiveResults with discovered services
        """
        logger.info(f"Starting active discovery for {len(subdomains)} subdomains")
        results = ActiveResults(total_probed=len(subdomains))

        # Phase 1: HTTP/HTTPS probing with httpx
        try:
            services = await self._probe_http_services(subdomains)
            results.services = services
            results.live_count = len(services)
            results.dead_count = results.total_probed - results.live_count

            logger.info(f"Active discovery complete: {results.live_count} live, "
                       f"{results.dead_count} dead")
        except Exception as e:
            logger.error(f"HTTP probing failed: {e}")
            results.services = []

        return results

    async def _probe_http_services(self, subdomains: List[str]) -> List[Service]:
        """Probe subdomains for HTTP/HTTPS services

        Args:
            subdomains: List of subdomains to probe

        Returns:
            List of discovered Service objects
        """
        logger.debug(f"Probing {len(subdomains)} subdomains with httpx")
        services = []

        try:
            # Run httpx with tech detection and JSON output
            output = await self.runner.run_httpx(
                targets=subdomains,
                timeout=self.config.httpx_timeout,
                tech_detect=True,
                follow_redirects=True,
                json_output=True
            )

            # Parse JSON output
            for line in output.strip().split('\n'):
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    service = self._parse_httpx_result(data)
                    if service:
                        services.append(service)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse httpx JSON: {e}")
                    continue

            logger.debug(f"Discovered {len(services)} live services")

        except Exception as e:
            logger.error(f"httpx execution failed: {e}")
            raise

        return services

    def _parse_httpx_result(self, data: Dict) -> Optional[Service]:
        """Parse httpx JSON result into Service object

        Args:
            data: httpx JSON output dictionary

        Returns:
            Service object or None if parsing fails
        """
        try:
            # Extract basic service info
            url = data.get('url')
            status_code = data.get('status_code')

            if not url or not status_code:
                return None

            # Extract metadata
            content_length = data.get('content_length')
            title = data.get('title')
            server = data.get('webserver')
            response_time_str = data.get('time')  # Response time as string (e.g., "250ms" or "1.5s")
            final_url = data.get('final_url')

            # Parse response time to milliseconds
            response_time = self._parse_response_time(response_time_str)

            # Parse technologies
            technologies = self._parse_technologies(data.get('tech', []))

            # Parse security headers
            security_headers = self._parse_security_headers(data.get('header', {}))

            # Parse TLS info
            tls_info = self._parse_tls_info(data.get('tls', {}))

            # Create Service object
            service = Service(
                url=url,
                status_code=status_code,
                content_length=content_length,
                title=title,
                server=server,
                technologies=technologies,
                security_headers=security_headers,
                tls_info=tls_info,
                response_time=response_time,  # Already in milliseconds from parser
                redirects_to=final_url if final_url != url else None,
                discovered_at=datetime.utcnow()
            )

            return service

        except Exception as e:
            logger.warning(f"Failed to parse httpx result: {e}")
            return None

    def _parse_response_time(self, time_str: Optional[str]) -> Optional[float]:
        """Parse httpx response time string to milliseconds

        Args:
            time_str: Response time string (e.g., "250ms", "1.5s", "250.429ms")

        Returns:
            Response time in milliseconds or None
        """
        if not time_str:
            return None

        try:
            # Remove whitespace
            time_str = time_str.strip()

            # Parse based on unit
            if time_str.endswith('ms'):
                # Already in milliseconds
                return float(time_str[:-2])
            elif time_str.endswith('s'):
                # Convert seconds to milliseconds
                return float(time_str[:-1]) * 1000
            else:
                # Try to parse as number (assume milliseconds)
                return float(time_str)

        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse response time '{time_str}': {e}")
            return None

    def _parse_technologies(self, tech_list: List[str]) -> List[Technology]:
        """Parse technology detection results

        Args:
            tech_list: List of detected technologies from httpx

        Returns:
            List of Technology objects
        """
        technologies = []

        for tech_str in tech_list:
            if not tech_str:
                continue

            # httpx tech format: "name:version" or just "name"
            parts = tech_str.split(':', 1)
            name = parts[0].strip()
            version = parts[1].strip() if len(parts) > 1 else None

            # Categorize technology (basic categorization)
            category = self._categorize_technology(name)

            technology = Technology(
                name=name,
                version=version,
                category=category,
                confidence=0.8,  # httpx tech detection is reliable
                detected_from=["headers", "response"]
            )
            technologies.append(technology)

        return technologies

    def _categorize_technology(self, name: str) -> str:
        """Categorize technology by name

        Args:
            name: Technology name

        Returns:
            Category string
        """
        name_lower = name.lower()

        # Web servers
        if any(ws in name_lower for ws in ['nginx', 'apache', 'iis', 'caddy', 'lighttpd']):
            return 'web_server'

        # Frameworks
        if any(fw in name_lower for fw in ['express', 'django', 'flask', 'rails', 'laravel',
                                             'spring', 'aspnet', 'nextjs', 'nuxt']):
            return 'framework'

        # CMS
        if any(cms in name_lower for cms in ['wordpress', 'drupal', 'joomla', 'magento',
                                               'shopify', 'wix']):
            return 'cms'

        # CDN
        if any(cdn in name_lower for cdn in ['cloudflare', 'akamai', 'fastly', 'cloudfront']):
            return 'cdn'

        # JavaScript libraries
        if any(js in name_lower for js in ['jquery', 'react', 'vue', 'angular', 'bootstrap']):
            return 'javascript'

        # Default
        return 'other'

    def _parse_security_headers(self, headers: Dict[str, str]) -> Optional[SecurityHeaders]:
        """Parse security headers from HTTP response

        Args:
            headers: HTTP response headers

        Returns:
            SecurityHeaders object or None
        """
        # Normalize header keys to lowercase
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # Extract security headers
        csp = headers_lower.get('content-security-policy')
        hsts = headers_lower.get('strict-transport-security')
        x_frame = headers_lower.get('x-frame-options')
        x_content_type = headers_lower.get('x-content-type-options')
        x_xss = headers_lower.get('x-xss-protection')
        referrer = headers_lower.get('referrer-policy')
        permissions = headers_lower.get('permissions-policy')

        # Only create SecurityHeaders if at least one header is present
        if any([csp, hsts, x_frame, x_content_type, x_xss, referrer, permissions]):
            return SecurityHeaders(
                content_security_policy=csp,
                strict_transport_security=hsts,
                x_frame_options=x_frame,
                x_content_type_options=x_content_type,
                x_xss_protection=x_xss,
                referrer_policy=referrer,
                permissions_policy=permissions
            )

        return None

    def _parse_tls_info(self, tls_data: Dict) -> Optional[TLSInfo]:
        """Parse TLS/SSL certificate information

        Args:
            tls_data: TLS information from httpx

        Returns:
            TLSInfo object or None
        """
        if not tls_data:
            return None

        try:
            # Extract TLS information
            version = tls_data.get('tls_version')
            cipher = tls_data.get('cipher')

            # Certificate info
            cert = tls_data.get('certificate', {})
            issuer = cert.get('issuer_cn')
            subject = cert.get('subject_cn')

            # Validity dates
            valid_from = cert.get('not_before')
            valid_to = cert.get('not_after')

            # Parse datetime strings
            if valid_from:
                valid_from = datetime.fromisoformat(valid_from.replace('Z', '+00:00'))
            if valid_to:
                valid_to = datetime.fromisoformat(valid_to.replace('Z', '+00:00'))

            # Subject Alternative Names
            san = cert.get('subject_an', [])

            # Check if expired or self-signed
            expired = False
            if valid_to:
                expired = datetime.utcnow() > valid_to.replace(tzinfo=None)

            self_signed = cert.get('self_signed', False)

            return TLSInfo(
                version=version,
                cipher=cipher,
                issuer=issuer,
                subject=subject,
                valid_from=valid_from,
                valid_to=valid_to,
                san=san if isinstance(san, list) else [],
                expired=expired,
                self_signed=self_signed
            )

        except Exception as e:
            logger.warning(f"Failed to parse TLS info: {e}")
            return None
