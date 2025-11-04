"""Data models for discovery results"""

from .domain import Subdomain, DNSRecords, DomainInfo
from .service import Service, Technology, SecurityHeaders
from .finding import Finding, CVE
from .discovery import DiscoveryResult, DiscoveryMetadata

__all__ = [
    'Subdomain', 'DNSRecords', 'DomainInfo',
    'Service', 'Technology', 'SecurityHeaders',
    'Finding', 'CVE',
    'DiscoveryResult', 'DiscoveryMetadata'
]
