"""Main discovery result models"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from .domain import DomainInfo
from .service import Service, Technology
from .finding import Finding


class DiscoveryStage(str, Enum):
    """Discovery pipeline stages"""
    INITIALIZED = "initialized"
    PASSIVE_DISCOVERY = "passive_discovery"
    ACTIVE_DISCOVERY = "active_discovery"
    DEEP_DISCOVERY = "deep_discovery"
    ENRICHMENT = "enrichment"
    COMPLETED = "completed"
    FAILED = "failed"


class TimelineEvent(BaseModel):
    """Timeline event during discovery"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stage: DiscoveryStage
    event: str = Field(..., description="Event description")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")


class DiscoveryMetadata(BaseModel):
    """Metadata about the discovery execution"""
    target: str = Field(..., description="Target URL/domain")
    scan_id: str = Field(..., description="Unique scan identifier")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    discovery_depth: str = Field(default="normal", description="Discovery depth level")
    tool_versions: Dict[str, str] = Field(
        default_factory=dict,
        description="Versions of tools used"
    )
    status: DiscoveryStage = Field(default=DiscoveryStage.INITIALIZED)
    error: Optional[str] = Field(default=None, description="Error message if failed")


class Endpoint(BaseModel):
    """Discovered API endpoint or URL path"""
    url: str = Field(..., description="Full endpoint URL")
    method: str = Field(default="GET", description="HTTP method")
    status_code: Optional[int] = Field(default=None, description="Response status")
    discovered_via: str = Field(..., description="Discovery source: crawl|js_analysis|sitemap|etc")
    parameters: List[str] = Field(default_factory=list, description="URL parameters")
    requires_auth: Optional[bool] = Field(default=None, description="Requires authentication")


class Recommendation(BaseModel):
    """Pentest focus recommendation"""
    category: str = Field(..., description="Recommendation category")
    priority: str = Field(..., description="Priority: high|medium|low")
    areas: List[str] = Field(..., description="Specific areas to focus on")
    rationale: Optional[str] = Field(default=None, description="Why this is recommended")


class Statistics(BaseModel):
    """Discovery statistics summary"""
    total_subdomains: int = 0
    live_services: int = 0
    technologies_detected: int = 0
    endpoints_discovered: int = 0
    findings_by_severity: Dict[str, int] = Field(
        default_factory=lambda: {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
    )
    coverage_completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Estimated discovery completeness"
    )


class DiscoveryResult(BaseModel):
    """Complete discovery result output"""
    metadata: DiscoveryMetadata = Field(..., description="Scan metadata")
    discovery_timeline: List[TimelineEvent] = Field(
        default_factory=list,
        description="Timeline of discovery events"
    )
    domains: Optional[DomainInfo] = Field(default=None, description="Domain intelligence")
    services: List[Service] = Field(default_factory=list, description="Live web services")
    technologies: List[Technology] = Field(default_factory=list, description="All detected technologies")
    endpoints: List[Endpoint] = Field(default_factory=list, description="Discovered endpoints")
    findings: List[Finding] = Field(default_factory=list, description="Security findings")
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="Pentest focus recommendations"
    )
    statistics: Statistics = Field(default_factory=Statistics, description="Summary statistics")

    def add_timeline_event(self, stage: DiscoveryStage, event: str, details: Optional[Dict[str, Any]] = None):
        """Add event to timeline"""
        self.discovery_timeline.append(
            TimelineEvent(stage=stage, event=event, details=details)
        )

    def update_statistics(self):
        """Recalculate statistics from current data"""
        if self.domains:
            self.statistics.total_subdomains = len(self.domains.subdomains)

        self.statistics.live_services = len(self.services)
        self.statistics.technologies_detected = len(self.technologies)
        self.statistics.endpoints_discovered = len(self.endpoints)

        # Count findings by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in self.findings:
            severity_counts[finding.severity.value] += 1
        self.statistics.findings_by_severity = severity_counts

        # Estimate completeness (simple heuristic for PoC)
        completeness_score = 0.0
        if self.domains and self.domains.total_subdomains > 0:
            completeness_score += 0.3
        if self.statistics.live_services > 0:
            completeness_score += 0.3
        if self.statistics.endpoints_discovered > 10:
            completeness_score += 0.2
        if self.statistics.technologies_detected > 0:
            completeness_score += 0.2

        self.statistics.coverage_completeness = min(completeness_score, 1.0)
