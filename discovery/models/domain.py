"""Domain and DNS related models"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class PortScanResult(BaseModel):
    """Port scan result for a single port"""
    port: int = Field(..., description="Port number (1-65535)")
    protocol: str = Field(default="tcp", description="Protocol (tcp/udp)")
    state: str = Field(..., description="Port state (open/closed/filtered)")
    service: Optional[str] = Field(default=None, description="Service name (http, ssh, etc.)")
    version: Optional[str] = Field(default=None, description="Service version if detected")
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class DNSRecords(BaseModel):
    """DNS records for a domain"""
    a: List[str] = Field(default_factory=list, description="A records (IPv4)")
    aaaa: List[str] = Field(default_factory=list, description="AAAA records (IPv6)")
    mx: List[str] = Field(default_factory=list, description="MX records")
    txt: List[str] = Field(default_factory=list, description="TXT records")
    ns: List[str] = Field(default_factory=list, description="NS records")
    cname: Optional[str] = Field(default=None, description="CNAME record")


class Subdomain(BaseModel):
    """Discovered subdomain information"""
    name: str = Field(..., description="Subdomain name")
    ips: List[str] = Field(default_factory=list, description="Resolved IP addresses")
    status: str = Field(default="unknown", description="Status: live|dead|unknown")
    dns_records: Optional[DNSRecords] = Field(default=None, description="DNS records")
    cloud_provider: Optional[str] = Field(default=None, description="Cloud provider if detected")
    cdn: Optional[str] = Field(default=None, description="CDN provider if detected")
    discovered_via: str = Field(..., description="Discovery source")
    discovered_at: datetime = Field(default_factory=datetime.utcnow)

    # Port scanning results
    open_ports: List[PortScanResult] = Field(default_factory=list, description="Open ports discovered")
    total_ports_scanned: int = Field(default=0, description="Total ports scanned")
    open_ports_count: int = Field(default=0, description="Count of open ports")


class WHOISData(BaseModel):
    """WHOIS registration data"""
    registrar: Optional[str] = None
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    name_servers: List[str] = Field(default_factory=list)
    status: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    raw_data: Optional[str] = Field(default=None, description="Raw WHOIS response")


class DomainInfo(BaseModel):
    """Complete domain intelligence"""
    root_domain: str = Field(..., description="Root domain being analyzed")
    subdomains: List[Subdomain] = Field(default_factory=list)
    dns_records: Optional[DNSRecords] = Field(default=None, description="Root domain DNS")
    whois: Optional[WHOISData] = None
    total_subdomains: int = Field(default=0, description="Total discovered subdomains")
    live_subdomains: int = Field(default=0, description="Live/responsive subdomains")
