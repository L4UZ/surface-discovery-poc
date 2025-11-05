"""Authentication configuration models"""
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class BasicAuth(BaseModel):
    """Basic authentication credentials"""
    username: str = Field(..., description="Username for basic auth")
    password: str = Field(..., description="Password for basic auth")


class AuthConfig(BaseModel):
    """Authentication configuration for a specific URL"""
    url: str = Field(..., description="Target URL requiring authentication")
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Custom headers for authentication (e.g., Authorization, X-API-Key)"
    )
    cookies: Optional[Dict[str, str]] = Field(
        default=None,
        description="Authentication cookies (e.g., session_id, csrf_token)"
    )
    basic: Optional[BasicAuth] = Field(
        default=None,
        description="Basic authentication credentials"
    )


class AuthenticationConfig(BaseModel):
    """Complete authentication configuration"""
    authentication: List[AuthConfig] = Field(
        default_factory=list,
        description="List of authentication configurations per URL"
    )
