# Phase 0: Deep URL Discovery - Quick Start Guide

**Get started with deep URL discovery implementation in 2 weeks**

## Prerequisites

```bash
# Install Playwright
pip install playwright>=1.40.0
playwright install chromium

# Verify installation
python -c "from playwright.sync_api import sync_playwright; print('Playwright ready!')"
```

## Week 1: Core Implementation (Days 1-5)

### Day 1: Project Structure & Basic Crawler (4 hours)

```bash
# Create directories
mkdir -p discovery/crawler
mkdir -p discovery/models
mkdir -p tests/crawler

# Create __init__ files
touch discovery/crawler/__init__.py
```

Create `discovery/crawler/deep_crawler.py`:

```python
"""Playwright-based deep URL discovery"""
from playwright.async_api import async_playwright, Browser, Page
from typing import List, Set, Dict, Optional
import asyncio
from urllib.parse import urljoin, urlparse

class DeepURLCrawler:
    """Comprehensive URL discovery with JavaScript execution"""

    def __init__(self, max_depth: int = 5, max_urls: int = 2000):
        self.max_depth = max_depth
        self.max_urls = max_urls
        self.visited_urls: Set[str] = set()
        self.discovered_urls: Set[str] = set()

    async def crawl(
        self,
        start_urls: List[str],
        auth_context: Optional[Dict] = None
    ) -> Set[str]:
        """
        Crawl URLs with full JavaScript execution

        Args:
            start_urls: List of URLs to start crawling from
            auth_context: Optional authentication (cookies, headers)

        Returns:
            Set of discovered URLs
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # Apply authentication if provided
            if auth_context:
                if 'cookies' in auth_context:
                    await context.add_cookies(auth_context['cookies'])
                if 'headers' in auth_context:
                    await context.set_extra_http_headers(auth_context['headers'])

            # Crawl each starting URL
            for url in start_urls:
                await self._crawl_url(context, url, depth=0)

            await browser.close()

        return self.discovered_urls

    async def _crawl_url(self, context, url: str, depth: int):
        """Recursively crawl a URL"""
        if depth > self.max_depth or len(self.discovered_urls) >= self.max_urls:
            return

        if url in self.visited_urls:
            return

        self.visited_urls.add(url)

        try:
            page = await context.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Extract URLs from page
            urls = await self._extract_urls(page, url)
            self.discovered_urls.update(urls)

            # Recursively crawl links (same domain only)
            for link in urls:
                if self._is_same_domain(url, link):
                    await self._crawl_url(context, link, depth + 1)

            await page.close()

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    async def _extract_urls(self, page: Page, base_url: str) -> Set[str]:
        """Extract all URLs from page"""
        urls = set()

        # Extract from links
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => a.href);
        }''')

        for link in links:
            normalized = urljoin(base_url, link)
            urls.add(normalized)

        return urls

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        return urlparse(url1).netloc == urlparse(url2).netloc
```

### Day 2: URL Extractor & Form Discovery (4 hours)

Create `discovery/crawler/url_extractor.py`:

```python
"""URL extraction and normalization utilities"""
from playwright.async_api import Page
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse, urlunparse

class URLExtractor:
    """Extract and normalize URLs from web pages"""

    @staticmethod
    async def extract_from_page(page: Page, base_url: str) -> Set[str]:
        """
        Extract all URLs from a page: links, forms, JavaScript navigation

        Args:
            page: Playwright Page object
            base_url: Base URL for relative link resolution

        Returns:
            Set of normalized absolute URLs
        """
        urls = set()

        # Extract from anchor tags
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => a.href);
        }''')
        urls.update(links)

        # Extract from forms (action URLs)
        form_actions = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('form[action]'))
                .map(form => form.action);
        }''')
        urls.update(form_actions)

        # Extract from JavaScript onclick handlers (basic)
        onclick_urls = await page.evaluate('''() => {
            const urlPattern = /(https?:\\/\\/[^\\s'"]+)/g;
            return Array.from(document.querySelectorAll('[onclick]'))
                .map(el => el.getAttribute('onclick'))
                .join(' ')
                .match(urlPattern) || [];
        }''')
        if onclick_urls:
            urls.update(onclick_urls)

        # Normalize all URLs
        normalized = {URLExtractor.normalize_url(url, base_url) for url in urls if url}

        return normalized

    @staticmethod
    async def extract_forms(page: Page) -> List[Dict]:
        """
        Discover forms and their POST endpoints

        Returns:
            List of form metadata dictionaries
        """
        forms = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('form')).map(form => ({
                action: form.action,
                method: form.method || 'GET',
                fields: Array.from(form.querySelectorAll('input, select, textarea'))
                    .map(field => ({
                        name: field.name,
                        type: field.type || field.tagName.toLowerCase(),
                        required: field.required
                    }))
            }));
        }''')

        return forms

    @staticmethod
    def normalize_url(url: str, base_url: str) -> str:
        """
        Normalize and resolve relative URLs

        Args:
            url: URL to normalize
            base_url: Base URL for relative resolution

        Returns:
            Normalized absolute URL
        """
        # Resolve relative URLs
        absolute = urljoin(base_url, url)

        # Parse and remove fragments
        parsed = urlparse(absolute)
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))

        return normalized
```

### Day 3: Data Models (3 hours)

Create `discovery/models/url.py`:

```python
"""URL discovery data models"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class DiscoveredURL(BaseModel):
    """Individual discovered URL"""
    url: str = Field(..., description="Full URL")
    method: str = Field(default="GET", description="HTTP method (GET, POST, etc.)")
    source_page: Optional[str] = Field(default=None, description="Page where URL was found")
    depth: int = Field(default=0, description="Crawl depth from start")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query params or form fields")
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    response_code: Optional[int] = Field(default=None, description="HTTP response code")
    content_type: Optional[str] = Field(default=None, description="Content-Type header")

class FormData(BaseModel):
    """Form metadata"""
    action_url: str = Field(..., description="Form action URL")
    method: str = Field(default="GET", description="Form submission method")
    fields: List[Dict[str, Any]] = Field(default_factory=list, description="Form fields")

class URLDiscoveryResult(BaseModel):
    """Results from URL discovery crawl"""
    urls: List[DiscoveredURL] = Field(default_factory=list)
    forms: List[FormData] = Field(default_factory=list)
    total_urls: int = Field(default=0)
    unique_urls: int = Field(default=0)
    crawl_depth_reached: int = Field(default=0)
    pages_visited: int = Field(default=0)
    forms_discovered: int = Field(default=0)
```

### Day 4-5: Integration with Stage 4 (8 hours)

Update `discovery/stages/deep.py`:

```python
# Add to imports
from ..crawler.deep_crawler import DeepURLCrawler
from ..crawler.url_extractor import URLExtractor
from ..models.url import DiscoveredURL, URLDiscoveryResult

class DeepDiscovery:
    """Enhanced deep discovery with intelligent crawler selection"""

    async def run(self, subdomains: List[Subdomain]) -> DeepDiscoveryResults:
        """
        Intelligent crawling based on depth configuration
        """
        # Get live URLs from httpx results
        live_urls = self._get_live_urls(subdomains)

        if not live_urls:
            logger.warning("No live URLs to crawl")
            return DeepDiscoveryResults()

        # Choose crawler based on depth
        if self.config.depth == "deep" and self.config.javascript_execution:
            logger.info("Using hybrid approach: katana + Playwright")
            # Fast sweep with katana
            katana_results = await self._run_katana(live_urls)

            # Deep crawl with Playwright
            playwright_results = await self._run_deep_crawler(live_urls)

            # Merge results
            return self._merge_results(katana_results, playwright_results)
        else:
            # Use katana only for speed
            logger.info("Using katana for fast crawling")
            return await self._run_katana(live_urls)

    async def _run_deep_crawler(self, urls: List[str]) -> URLDiscoveryResult:
        """Run Playwright-based deep crawler"""
        crawler = DeepURLCrawler(
            max_depth=self.config.max_crawl_depth,
            max_urls=self.config.max_urls_per_domain
        )

        # Pass authentication context if available
        auth_context = None
        if hasattr(self.config, 'auth_config'):
            auth_context = self.config.auth_config

        discovered = await crawler.crawl(urls, auth_context=auth_context)

        # Convert to DiscoveredURL objects
        url_objects = [
            DiscoveredURL(
                url=url,
                discovered_at=datetime.utcnow()
            )
            for url in discovered
        ]

        return URLDiscoveryResult(
            urls=url_objects,
            total_urls=len(discovered),
            unique_urls=len(discovered),
            pages_visited=len(crawler.visited_urls)
        )
```

## Week 2: Testing & Integration (Days 6-10)

### Day 6-7: Unit Tests (8 hours)

Create `tests/crawler/test_url_extractor.py`:

```python
"""Tests for URL extraction"""
import pytest
from discovery.crawler.url_extractor import URLExtractor

def test_normalize_url():
    """Test URL normalization"""
    base = "https://example.com/page"

    # Relative URL
    assert URLExtractor.normalize_url("./other", base) == "https://example.com/other"

    # Absolute URL
    assert URLExtractor.normalize_url("https://example.com/test", base) == "https://example.com/test"

    # Remove fragment
    assert URLExtractor.normalize_url("https://example.com/page#section", base) == "https://example.com/page"

@pytest.mark.asyncio
async def test_extract_forms():
    """Test form extraction"""
    # Would use Playwright page fixture
    pass  # Implement with real Playwright page
```

### Day 8-9: Configuration & Documentation (8 hours)

Update `discovery/config.py`:

```python
class DiscoveryConfig(BaseModel):
    # ... existing fields ...

    # Deep crawling configuration
    max_crawl_depth: int = Field(default=3, description="Maximum crawl depth")
    max_urls_per_domain: int = Field(default=500, description="Max URLs per domain")
    form_interaction: bool = Field(default=False, description="Enable form submission")
    javascript_execution: bool = Field(default=False, description="Enable JS execution")
    crawl_timeout: int = Field(default=600, description="Crawl timeout in seconds")

# Update depth presets
DEPTH_CONFIGS = {
    "shallow": DiscoveryConfig(
        max_crawl_depth=2,
        max_urls_per_domain=100,
        javascript_execution=False,
        # ... other shallow config ...
    ),
    "normal": DiscoveryConfig(
        max_crawl_depth=3,
        max_urls_per_domain=500,
        javascript_execution=False,
        # ... other normal config ...
    ),
    "deep": DiscoveryConfig(
        max_crawl_depth=5,
        max_urls_per_domain=2000,
        javascript_execution=True,  # Enable Playwright in deep mode
        form_interaction=True,
        # ... other deep config ...
    ),
}
```

### Day 10: Docker & Final Testing (4 hours)

Update `Dockerfile`:

```dockerfile
# Install Playwright and browsers
RUN pip install playwright>=1.40.0
RUN playwright install chromium --with-deps

# Note: Adds ~300MB to image size
```

Update `requirements.txt`:

```
playwright>=1.40.0
```

Test the complete integration:

```bash
# Rebuild Docker image
docker build -t surface-discovery:latest .

# Test deep mode
docker run --rm \
  -v $(pwd)/output:/output \
  surface-discovery:latest \
  --url https://example.com \
  --depth deep \
  --output /output/deep-test.json
```

## Success Checklist

- ✅ Playwright installed and working
- ✅ DeepURLCrawler extracts URLs with JavaScript
- ✅ URLExtractor finds forms and normalizes URLs
- ✅ Data models (DiscoveredURL, URLDiscoveryResult) implemented
- ✅ Stage 4 enhanced with hybrid crawler selection
- ✅ Configuration depth presets updated
- ✅ Docker image builds with Playwright
- ✅ Deep mode successfully crawls test SPA

## Next Steps

After Phase 0 completion:
1. Document deep crawling features in README.md
2. Create `docs/DEEP_URL_DISCOVERY.md` user guide
3. Proceed to **Phase 1: Tool Abstraction Layer** (Weeks 3-4)

## Troubleshooting

### Playwright Installation Issues

```bash
# If browsers fail to install
playwright install chromium --force

# Check Playwright version
python -c "import playwright; print(playwright.__version__)"
```

### Docker Build Issues

```bash
# If image size is a concern, use playwright-python without browsers
# Then rely on host browser (not recommended for production)
```

### Performance Issues

```bash
# Reduce max_urls_per_domain if crawls are too slow
# Use --depth normal instead of deep for faster scans
```

---

**Estimated Time:** 80 hours over 2 weeks
**Next Phase:** Phase 1 - Tool Abstraction Layer (see AGENT_QUICKSTART.md)
