"""Data models for discovery results"""

from .domain import Subdomain, DNSRecords, DomainInfo, WHOISData, PortScanResult
from .service import Service, Technology, SecurityHeaders, TLSInfo
from .finding import Finding, CVE
from .discovery import DiscoveryResult, DiscoveryMetadata, DiscoveryStage, Endpoint
from .auth import AuthConfig, AuthenticationConfig, BasicAuth
from .url import DiscoveredURL, FormData, URLDiscoveryResult

__all__ = [
    'Subdomain', 'DNSRecords', 'DomainInfo', 'WHOISData', 'PortScanResult',
    'Service', 'Technology', 'SecurityHeaders', 'TLSInfo',
    'Finding', 'CVE',
    'DiscoveryResult', 'DiscoveryMetadata', 'DiscoveryStage', 'Endpoint',
    'AuthConfig', 'AuthenticationConfig', 'BasicAuth',
    'DiscoveredURL', 'FormData', 'URLDiscoveryResult'
]
