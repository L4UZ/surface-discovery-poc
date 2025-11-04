"""Service and technology detection models"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class SecurityHeaders(BaseModel):
    """HTTP security headers analysis"""
    content_security_policy: Optional[str] = Field(default=None, alias="csp")
    strict_transport_security: Optional[str] = Field(default=None, alias="hsts")
    x_frame_options: Optional[str] = Field(default=None, alias="x_frame")
    x_content_type_options: Optional[str] = Field(default=None, alias="x_content_type")
    x_xss_protection: Optional[str] = Field(default=None, alias="x_xss")
    referrer_policy: Optional[str] = None
    permissions_policy: Optional[str] = None

    class Config:
        populate_by_name = True


class TLSInfo(BaseModel):
    """TLS/SSL certificate information"""
    version: Optional[str] = None
    cipher: Optional[str] = None
    issuer: Optional[str] = None
    subject: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    san: List[str] = Field(default_factory=list, description="Subject Alternative Names")
    expired: bool = False
    self_signed: bool = False


class Technology(BaseModel):
    """Detected technology/framework"""
    name: str = Field(..., description="Technology name")
    version: Optional[str] = Field(default=None, description="Version if detected")
    category: str = Field(..., description="Category: web_server|framework|cms|library|etc")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Detection confidence")
    detected_from: List[str] = Field(
        default_factory=list,
        description="Detection sources: headers|cookies|meta|javascript|etc"
    )


class Service(BaseModel):
    """Live web service information"""
    url: str = Field(..., description="Service URL")
    status_code: int = Field(..., description="HTTP status code")
    content_length: Optional[int] = Field(default=None, description="Response size in bytes")
    title: Optional[str] = Field(default=None, description="Page title")
    server: Optional[str] = Field(default=None, description="Server header value")
    technologies: List[Technology] = Field(default_factory=list)
    security_headers: Optional[SecurityHeaders] = None
    tls_info: Optional[TLSInfo] = None
    response_time: Optional[float] = Field(default=None, description="Response time in ms")
    redirects_to: Optional[str] = Field(default=None, description="Final URL after redirects")
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
