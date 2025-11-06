"""URL discovery data models for deep crawling with Playwright"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime


class DiscoveredURL(BaseModel):
    """Individual discovered URL from deep crawling"""
    url: str = Field(..., description="Full URL")
    method: str = Field(default="GET", description="HTTP method (GET, POST, etc.)")
    source_page: Optional[str] = Field(default=None, description="Page where URL was found")
    depth: int = Field(default=0, description="Crawl depth from start")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query params or form fields")
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    response_code: Optional[int] = Field(default=None, description="HTTP response code")
    content_type: Optional[str] = Field(default=None, description="Content-Type header")
    discovered_via: str = Field(default="deep_crawl", description="Discovery method: deep_crawl|form|js_analysis")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FormData(BaseModel):
    """Form metadata discovered during crawling"""
    action_url: str = Field(..., description="Form action URL")
    method: str = Field(default="GET", description="Form submission method")
    fields: List[Dict[str, Any]] = Field(default_factory=list, description="Form fields with metadata")
    source_page: Optional[str] = Field(default=None, description="Page containing the form")
    requires_auth: Optional[bool] = Field(default=None, description="Whether form requires authentication")

    class Config:
        arbitrary_types_allowed = True


class URLDiscoveryResult(BaseModel):
    """Results from URL discovery crawl using Playwright"""
    urls: List[DiscoveredURL] = Field(default_factory=list, description="All discovered URLs")
    forms: List[FormData] = Field(default_factory=list, description="Discovered forms")
    total_urls: int = Field(default=0, description="Total URLs discovered")
    unique_urls: int = Field(default=0, description="Unique URLs (deduplicated)")
    crawl_depth_reached: int = Field(default=0, description="Maximum crawl depth reached")
    pages_visited: int = Field(default=0, description="Total pages visited during crawl")
    forms_discovered: int = Field(default=0, description="Total forms found")
    api_endpoints: Set[str] = Field(default_factory=set, description="Potential API endpoints discovered")
    javascript_urls: int = Field(default=0, description="URLs discovered via JavaScript analysis")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            set: list,  # Convert sets to lists for JSON serialization
            datetime: lambda v: v.isoformat()
        }

    def add_url(self, url: DiscoveredURL):
        """Add a discovered URL to results"""
        self.urls.append(url)
        self.total_urls += 1

    def add_form(self, form: FormData):
        """Add a discovered form to results"""
        self.forms.append(form)
        self.forms_discovered += 1

    def get_unique_paths(self) -> Set[str]:
        """Extract unique URL paths from discovered URLs"""
        from urllib.parse import urlparse
        return {urlparse(url.url).path for url in self.urls}

    def get_urls_by_depth(self, depth: int) -> List[DiscoveredURL]:
        """Get URLs discovered at specific depth"""
        return [url for url in self.urls if url.depth == depth]

    def get_post_endpoints(self) -> List[DiscoveredURL]:
        """Get all POST endpoints discovered"""
        return [url for url in self.urls if url.method == "POST"]

    def get_forms_by_method(self, method: str) -> List[FormData]:
        """Get forms filtered by HTTP method"""
        return [form for form in self.forms if form.method.upper() == method.upper()]
