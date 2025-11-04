"""Parsers for external tool outputs"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import Subdomain, Service, Technology, DNSRecords, SecurityHeaders

logger = logging.getLogger(__name__)


class SubfinderParser:
    """Parse subfinder output"""

    @staticmethod
    def parse(output: str) -> List[str]:
        """Parse subfinder output to list of subdomains

        Args:
            output: Raw subfinder stdout (one subdomain per line)

        Returns:
            List of discovered subdomains
        """
        subdomains = []
        for line in output.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                subdomains.append(line)

        logger.debug(f"Parsed {len(subdomains)} subdomains from subfinder")
        return subdomains


class HTTPXParser:
    """Parse httpx JSON output"""

    @staticmethod
    def parse(output: str) -> List[Service]:
        """Parse httpx JSON output to Service objects

        Args:
            output: Raw httpx JSON output (one JSON object per line)

        Returns:
            List of Service objects
        """
        services = []

        for line in output.strip().split('\n'):
            if not line.strip():
                continue

            try:
                data = json.loads(line)
                service = HTTPXParser._parse_service(data)
                if service:
                    services.append(service)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse httpx JSON line: {e}")
                continue
            except Exception as e:
                logger.error(f"Error parsing httpx output: {e}")
                continue

        logger.debug(f"Parsed {len(services)} services from httpx")
        return services

    @staticmethod
    def _parse_service(data: Dict[str, Any]) -> Optional[Service]:
        """Convert httpx JSON object to Service model"""
        try:
            # Extract technologies
            technologies = []
            if 'tech' in data and data['tech']:
                for tech_name in data['tech']:
                    tech = Technology(
                        name=tech_name,
                        category="web",  # Default category
                        detected_from=["httpx"]
                    )
                    technologies.append(tech)

            # Extract security headers
            security_headers = None
            if 'header' in data:
                headers = data['header']
                security_headers = SecurityHeaders(
                    csp=headers.get('content-security-policy'),
                    hsts=headers.get('strict-transport-security'),
                    x_frame=headers.get('x-frame-options'),
                    x_content_type=headers.get('x-content-type-options'),
                    x_xss=headers.get('x-xss-protection'),
                    referrer_policy=headers.get('referrer-policy'),
                    permissions_policy=headers.get('permissions-policy')
                )

            # Build Service object
            service = Service(
                url=data.get('url', ''),
                status_code=data.get('status_code', 0),
                content_length=data.get('content_length'),
                title=data.get('title'),
                server=data.get('webserver'),
                technologies=technologies,
                security_headers=security_headers,
                response_time=data.get('time'),
                redirects_to=data.get('final_url')
            )

            return service

        except Exception as e:
            logger.error(f"Error creating Service from httpx data: {e}")
            return None


class DNSXParser:
    """Parse dnsx JSON output"""

    @staticmethod
    def parse(output: str) -> Dict[str, DNSRecords]:
        """Parse dnsx JSON output to DNS records

        Args:
            output: Raw dnsx JSON output (one JSON object per line)

        Returns:
            Dict mapping hostnames to DNSRecords
        """
        dns_data = {}

        for line in output.strip().split('\n'):
            if not line.strip():
                continue

            try:
                data = json.loads(line)
                hostname = data.get('host', '')
                if not hostname:
                    continue

                # Initialize or get existing records
                if hostname not in dns_data:
                    dns_data[hostname] = DNSRecords()

                # Parse different record types
                if 'a' in data and data['a']:
                    dns_data[hostname].a.extend(data['a'])

                if 'aaaa' in data and data['aaaa']:
                    dns_data[hostname].aaaa.extend(data['aaaa'])

                if 'mx' in data and data['mx']:
                    dns_data[hostname].mx.extend(data['mx'])

                if 'txt' in data and data['txt']:
                    dns_data[hostname].txt.extend(data['txt'])

                if 'ns' in data and data['ns']:
                    dns_data[hostname].ns.extend(data['ns'])

                if 'cname' in data and data['cname']:
                    dns_data[hostname].cname = data['cname'][0] if data['cname'] else None

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse dnsx JSON line: {e}")
                continue
            except Exception as e:
                logger.error(f"Error parsing dnsx output: {e}")
                continue

        logger.debug(f"Parsed DNS records for {len(dns_data)} hosts")
        return dns_data


class NucleiParser:
    """Parse nuclei JSON output"""

    @staticmethod
    def parse(output: str) -> List[Dict[str, Any]]:
        """Parse nuclei JSON output to finding data

        Args:
            output: Raw nuclei JSON output (one JSON object per line)

        Returns:
            List of finding dictionaries
        """
        findings = []

        for line in output.strip().split('\n'):
            if not line.strip():
                continue

            try:
                data = json.loads(line)
                finding = {
                    'template_id': data.get('template-id', ''),
                    'name': data.get('info', {}).get('name', ''),
                    'severity': data.get('info', {}).get('severity', 'info'),
                    'description': data.get('info', {}).get('description', ''),
                    'matched_at': data.get('matched-at', ''),
                    'extracted_results': data.get('extracted-results', []),
                    'type': data.get('type', ''),
                    'timestamp': datetime.utcnow().isoformat()
                }
                findings.append(finding)

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse nuclei JSON line: {e}")
                continue
            except Exception as e:
                logger.error(f"Error parsing nuclei output: {e}")
                continue

        logger.debug(f"Parsed {len(findings)} findings from nuclei")
        return findings


def parse_subdomain_list(raw_output: str) -> List[str]:
    """Generic parser for line-separated subdomain lists

    Args:
        raw_output: Raw tool output with one subdomain per line

    Returns:
        List of unique subdomains
    """
    subdomains = set()

    for line in raw_output.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith(('#', '//', ';')):
            # Remove protocol if present
            if '://' in line:
                line = line.split('://', 1)[1]
            # Remove path if present
            if '/' in line:
                line = line.split('/', 1)[0]
            # Remove port if present
            if ':' in line and not line.count(':') > 1:  # Not IPv6
                line = line.split(':', 1)[0]

            subdomains.add(line.lower())

    return sorted(list(subdomains))
