"""Configuration management for discovery service"""
from typing import Optional
from pydantic import BaseModel, Field


class DiscoveryConfig(BaseModel):
    """Configuration for discovery execution"""

    # Execution settings
    depth: str = Field(default="normal", description="Discovery depth: shallow|normal|deep")
    timeout: int = Field(default=600, description="Max execution time in seconds")
    parallel: int = Field(default=10, description="Max parallel tasks")

    # Tool timeouts (seconds)
    subfinder_timeout: int = 180
    dnsx_timeout: int = 120
    httpx_timeout: int = 180
    nuclei_timeout: int = 180
    katana_timeout: int = 120
    naabu_timeout: int = 120

    # Port scanning settings
    port_scan_rate: int = Field(default=1000, description="Packets per second for port scanning")

    # Discovery limits
    max_subdomains: Optional[int] = Field(default=None, description="Max subdomains to process")
    max_crawl_services: int = Field(default=10, description="Max services to crawl deeply")
    crawl_depth: int = Field(default=3, description="Web crawling depth")

    # Deep URL Discovery (Phase 0 - Playwright)
    max_crawl_depth: int = Field(default=3, description="Maximum depth for deep crawler")
    max_urls_per_domain: int = Field(default=500, description="Max URLs per domain")
    form_interaction: bool = Field(default=False, description="Enable form submission and interaction")
    javascript_execution: bool = Field(default=False, description="Enable JavaScript execution with Playwright")
    crawl_timeout: int = Field(default=600, description="Deep crawl timeout in seconds")

    # Rate limiting
    http_rate_limit: int = Field(default=50, description="HTTP requests per second")
    dns_rate_limit: int = Field(default=100, description="DNS queries per second")

    # Output settings
    verbose: bool = Field(default=False, description="Enable verbose logging")

    # Stage toggles
    skip_vuln_scan: bool = Field(default=False, description="Skip vulnerability scanning stage")

    class Config:
        frozen = True  # Immutable after creation


# Depth presets
DEPTH_CONFIGS = {
    "shallow": DiscoveryConfig(
        depth="shallow",
        timeout=300,
        parallel=5,
        subfinder_timeout=60,
        naabu_timeout=90,
        port_scan_rate=1000,
        max_subdomains=20,
        max_crawl_services=3,
        crawl_depth=2,
        # Deep crawler settings (Phase 0)
        max_crawl_depth=2,
        max_urls_per_domain=100,
        form_interaction=False,
        javascript_execution=False,
        crawl_timeout=300
    ),
    "normal": DiscoveryConfig(
        depth="normal",
        timeout=600,
        parallel=10,
        naabu_timeout=180,
        port_scan_rate=1500,
        max_crawl_services=10,
        crawl_depth=3,
        # Deep crawler settings (Phase 0)
        max_crawl_depth=3,
        max_urls_per_domain=500,
        form_interaction=False,
        javascript_execution=False,
        crawl_timeout=600
    ),
    "deep": DiscoveryConfig(
        depth="deep",
        timeout=900,
        parallel=15,
        subfinder_timeout=300,
        naabu_timeout=900,  # Increased from 300s to 900s (15 min) for full port range scans
        port_scan_rate=2000,
        max_crawl_services=20,
        crawl_depth=5,
        # Deep crawler settings (Phase 0)
        max_crawl_depth=5,
        max_urls_per_domain=2000,
        form_interaction=True,
        javascript_execution=True,  # Enable Playwright in deep mode
        crawl_timeout=1200
    )
}


def get_config(depth: str = "normal", **overrides) -> DiscoveryConfig:
    """Get configuration with optional overrides"""
    base_config = DEPTH_CONFIGS.get(depth, DEPTH_CONFIGS["normal"])

    if overrides:
        # Create new config with overrides
        config_dict = base_config.model_dump()
        config_dict.update(overrides)
        return DiscoveryConfig(**config_dict)

    return base_config
