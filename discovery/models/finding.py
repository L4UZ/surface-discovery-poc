"""Security findings and vulnerability models"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    """Finding severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingType(str, Enum):
    """Types of findings"""
    SENSITIVE_FILE = "sensitive_file"
    MISCONFIGURATION = "misconfiguration"
    OUTDATED_SOFTWARE = "outdated_software"
    WEAK_TLS = "weak_tls"
    MISSING_HEADER = "missing_header"
    INFORMATION_DISCLOSURE = "information_disclosure"
    VULNERABLE_COMPONENT = "vulnerable_component"
    OTHER = "other"


class CVE(BaseModel):
    """CVE vulnerability information"""
    cve_id: str = Field(..., description="CVE identifier")
    severity: Severity = Field(..., description="CVSS severity")
    score: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="CVSS score")
    description: Optional[str] = None
    published_date: Optional[datetime] = None
    references: List[str] = Field(default_factory=list, description="Reference URLs")
    affected_versions: List[str] = Field(
        default_factory=list,
        description="Affected software versions"
    )


class Finding(BaseModel):
    """Security finding or vulnerability"""
    id: str = Field(..., description="Unique finding identifier")
    type: FindingType = Field(..., description="Finding category")
    severity: Severity = Field(..., description="Severity level")
    title: str = Field(..., description="Short finding description")
    description: str = Field(..., description="Detailed finding description")
    affected_url: Optional[str] = Field(default=None, description="Affected URL/endpoint")
    affected_component: Optional[str] = Field(
        default=None,
        description="Affected software component"
    )
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supporting evidence (screenshots, responses, etc.)"
    )
    recommendation: str = Field(..., description="Remediation recommendation")
    references: List[str] = Field(default_factory=list, description="Reference URLs/CVEs")
    cves: List[CVE] = Field(default_factory=list, description="Related CVEs")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Calculated risk score")
    discovered_at: datetime = Field(default_factory=datetime.utcnow)

    def to_summary(self) -> str:
        """Generate one-line summary"""
        return f"[{self.severity.value.upper()}] {self.title} - {self.affected_url or self.affected_component}"
