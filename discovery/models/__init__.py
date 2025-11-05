"""Data models for discovery results"""

from .domain import Subdomain, DNSRecords, DomainInfo, WHOISData
from .service import Service, Technology, SecurityHeaders, TLSInfo
from .finding import Finding, CVE
from .discovery import DiscoveryResult, DiscoveryMetadata, DiscoveryStage, Endpoint

__all__ = [
    'Subdomain', 'DNSRecords', 'DomainInfo', 'WHOISData',
    'Service', 'Technology', 'SecurityHeaders', 'TLSInfo',
    'Finding', 'CVE',
    'DiscoveryResult', 'DiscoveryMetadata', 'DiscoveryStage', 'Endpoint'
]
