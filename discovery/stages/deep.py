"""Deep discovery stage - web crawling and endpoint discovery"""
import asyncio
import json
import logging
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from pydantic import BaseModel, Field

from ..tools.runner import ToolRunner
from ..models import Endpoint, Service
from ..models.url import DiscoveredURL, URLDiscoveryResult, FormData
from ..crawler.deep_crawler import DeepURLCrawler
from ..crawler.url_extractor import URLExtractor
from ..config import DiscoveryConfig

logger = logging.getLogger(__name__)


class DeepResults(BaseModel):
    """Results from deep discovery stage"""
    endpoints: List[Endpoint] = Field(default_factory=list, description="Discovered endpoints")
    total_endpoints: int = 0
    unique_paths: Set[str] = Field(default_factory=set)
    crawled_services: int = 0
    # Phase 0: Deep URL Discovery results
    url_discovery: Optional[URLDiscoveryResult] = Field(default=None, description="Deep crawler results")
    crawler_used: str = Field(default="katana", description="Crawler type: katana|playwright|hybrid")

    class Config:
        arbitrary_types_allowed = True


class DeepDiscovery:
    """Deep reconnaissance stage - web crawling and endpoint expansion"""

    def __init__(self, config: DiscoveryConfig):
        """
        Args:
            config: Discovery configuration
        """
        self.config = config
        self.runner = ToolRunner(timeout=config.katana_timeout if hasattr(config, 'katana_timeout') else 300)

    async def run(self, services: List[Service]) -> DeepResults:
        """Execute deep discovery stage with intelligent crawler selection

        Args:
            services: List of live services to crawl

        Returns:
            DeepResults with discovered endpoints
        """
        logger.info(f"Starting deep discovery for {len(services)} services")
        results = DeepResults()

        # Extract base URLs from services
        urls = [service.url for service in services]

        if not urls:
            logger.warning("No services to crawl, skipping deep discovery")
            return results

        # Choose crawler based on depth configuration (Phase 0: Hybrid Strategy)
        if self.config.depth == "deep" and self.config.javascript_execution:
            logger.info("Using hybrid approach: katana + Playwright deep crawler")
            results.crawler_used = "hybrid"

            # Fast sweep with katana
            try:
                katana_endpoints = await self._crawl_services(urls)
                results.endpoints.extend(katana_endpoints)
                logger.info(f"Katana discovered {len(katana_endpoints)} endpoints")
            except Exception as e:
                logger.error(f"Katana crawling failed: {e}")

            # Deep crawl with Playwright for SPAs and forms
            try:
                playwright_results = await self._run_deep_crawler(urls)
                results.url_discovery = playwright_results

                # Convert deep crawler results to endpoints
                for discovered_url in playwright_results.urls:
                    endpoint = Endpoint(
                        url=discovered_url.url,
                        method=discovered_url.method,
                        status_code=discovered_url.response_code,
                        discovered_via=discovered_url.discovered_via,
                        parameters=list(discovered_url.parameters.keys()),
                        requires_auth=None
                    )
                    results.endpoints.append(endpoint)

                logger.info(f"Playwright discovered {len(playwright_results.urls)} URLs, "
                          f"{len(playwright_results.forms)} forms")
            except Exception as e:
                logger.error(f"Playwright deep crawling failed: {e}")
        else:
            # Use katana only for speed (shallow/normal modes)
            logger.info("Using katana for fast crawling")
            results.crawler_used = "katana"
            try:
                endpoints = await self._crawl_services(urls)
                results.endpoints = endpoints
            except Exception as e:
                logger.error(f"Katana crawling failed: {e}")
                results.endpoints = []

        # Calculate final statistics
        results.total_endpoints = len(results.endpoints)
        results.unique_paths = {self._extract_path(ep.url) for ep in results.endpoints}
        results.crawled_services = len(urls)

        logger.info(f"Deep discovery complete: {results.total_endpoints} endpoints, "
                   f"{len(results.unique_paths)} unique paths (crawler: {results.crawler_used})")

        return results

    async def _crawl_services(self, urls: List[str]) -> List[Endpoint]:
        """Crawl services for endpoints using katana

        Args:
            urls: List of service URLs to crawl

        Returns:
            List of discovered Endpoint objects
        """
        logger.debug(f"Crawling {len(urls)} services with katana")
        endpoints = []
        seen_urls = set()

        try:
            # Run katana with JSON output
            output = await self.runner.run_katana(
                targets=urls,
                depth=2,  # Crawl depth
                js_crawl=True,  # JavaScript analysis
                timeout=self.config.katana_timeout if hasattr(self.config, 'katana_timeout') else 300
            )

            # Parse JSONL output
            for line in output.strip().split('\n'):
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    endpoint = self._parse_katana_result(data)

                    # Deduplicate by URL
                    if endpoint and endpoint.url not in seen_urls:
                        endpoints.append(endpoint)
                        seen_urls.add(endpoint.url)

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse katana JSON: {e}")
                    continue

            logger.debug(f"Discovered {len(endpoints)} unique endpoints")

        except Exception as e:
            logger.error(f"katana execution failed: {e}")
            raise

        return endpoints

    def _parse_katana_result(self, data: Dict) -> Optional[Endpoint]:
        """Parse katana JSON result into Endpoint object

        Args:
            data: katana JSON output dictionary

        Returns:
            Endpoint object or None if parsing fails
        """
        try:
            # Extract request info
            request = data.get('request', {})
            response = data.get('response', {})

            method = request.get('method', 'GET')
            url = request.get('endpoint')

            if not url:
                return None

            # Extract status code from response
            status_code = response.get('status_code')

            # Extract URL parameters
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            parameters = list(query_params.keys())

            # Determine discovery source
            discovered_via = 'crawl'
            if data.get('source') == 'javascript':
                discovered_via = 'js_analysis'

            # Create Endpoint object
            endpoint = Endpoint(
                url=url,
                method=method,
                status_code=status_code,
                discovered_via=discovered_via,
                parameters=parameters,
                requires_auth=None  # Cannot determine from crawling alone
            )

            return endpoint

        except Exception as e:
            logger.warning(f"Failed to parse katana result: {e}")
            return None

    def _extract_path(self, url: str) -> str:
        """Extract path from URL for deduplication

        Args:
            url: Full URL

        Returns:
            URL path (e.g., /api/v1/users)
        """
        try:
            parsed = urlparse(url)
            return parsed.path or '/'
        except Exception:
            return '/'

    async def _run_deep_crawler(self, urls: List[str], auth_context: Optional[Dict] = None) -> URLDiscoveryResult:
        """Run Playwright-based deep crawler for SPAs and dynamic sites

        Args:
            urls: List of URLs to crawl
            auth_context: Optional authentication context (cookies, headers)

        Returns:
            URLDiscoveryResult with comprehensive URL discovery
        """
        logger.debug(f"Running deep crawler (Playwright) for {len(urls)} URLs")

        # Initialize deep crawler
        crawler = DeepURLCrawler(
            max_depth=self.config.max_crawl_depth,
            max_urls=self.config.max_urls_per_domain
        )

        # Crawl URLs with JavaScript execution
        discovered_urls = await crawler.crawl(urls, auth_context=auth_context)

        # Convert discovered URLs to DiscoveredURL objects
        url_objects = [
            DiscoveredURL(
                url=url,
                discovered_at=datetime.now(datetime.timezone.utc),
                discovered_via="deep_crawl"
            )
            for url in discovered_urls
        ]

        # Build result
        result = URLDiscoveryResult(
            urls=url_objects,
            total_urls=len(discovered_urls),
            unique_urls=len(discovered_urls),
            pages_visited=len(crawler.visited_urls),
            crawl_depth_reached=crawler.max_depth
        )

        return result
