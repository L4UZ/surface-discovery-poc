"""Playwright-based deep URL discovery with JavaScript execution"""
import asyncio
import logging
from typing import List, Set, Dict, Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = logging.getLogger(__name__)


class DeepURLCrawler:
    """Comprehensive URL discovery with JavaScript execution support"""

    def __init__(self, max_depth: int = 5, max_urls: int = 2000):
        """
        Initialize deep URL crawler

        Args:
            max_depth: Maximum crawl depth from starting URLs
            max_urls: Maximum total URLs to discover
        """
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
        if not start_urls:
            logger.warning("No start URLs provided")
            return self.discovered_urls

        logger.info(f"Starting deep crawl of {len(start_urls)} URLs (depth={self.max_depth}, max={self.max_urls})")

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
                try:
                    await self._crawl_url(context, url, depth=0)
                except Exception as e:
                    logger.error(f"Error crawling {url}: {e}")
                    continue

                # Check if we've hit the URL limit
                if len(self.discovered_urls) >= self.max_urls:
                    logger.info(f"Reached max URLs limit ({self.max_urls}), stopping crawl")
                    break

            await browser.close()

        logger.info(f"Deep crawl complete: discovered {len(self.discovered_urls)} URLs, visited {len(self.visited_urls)} pages")
        return self.discovered_urls

    async def _crawl_url(self, context: BrowserContext, url: str, depth: int):
        """
        Recursively crawl a URL

        Args:
            context: Playwright browser context
            url: URL to crawl
            depth: Current depth from starting URL
        """
        # Check stopping conditions
        if depth > self.max_depth:
            logger.debug(f"Skipping {url}: max depth reached")
            return

        if len(self.discovered_urls) >= self.max_urls:
            logger.debug(f"Skipping {url}: max URLs reached")
            return

        if url in self.visited_urls:
            logger.debug(f"Skipping {url}: already visited")
            return

        self.visited_urls.add(url)

        try:
            page = await context.new_page()

            # Navigate with networkidle for JavaScript apps
            logger.debug(f"Crawling {url} at depth {depth}")
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Extract URLs from page
            urls = await self._extract_urls(page, url)
            self.discovered_urls.update(urls)

            logger.debug(f"Discovered {len(urls)} URLs from {url}")

            # Recursively crawl links (same domain only)
            for link in urls:
                if self._is_same_domain(url, link):
                    await self._crawl_url(context, link, depth + 1)

                # Check if we've hit the URL limit
                if len(self.discovered_urls) >= self.max_urls:
                    break

            await page.close()

        except Exception as e:
            logger.warning(f"Failed to crawl {url}: {e}")

    async def _extract_urls(self, page: Page, base_url: str) -> Set[str]:
        """
        Extract all URLs from page using JavaScript

        Args:
            page: Playwright Page object
            base_url: Base URL for relative link resolution

        Returns:
            Set of normalized absolute URLs
        """
        urls = set()

        try:
            # Extract from anchor tags
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href);
            }''')

            for link in links:
                normalized = urljoin(base_url, link)
                urls.add(normalized)

            # Extract from forms (action URLs)
            form_actions = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('form[action]'))
                    .map(form => form.action);
            }''')

            for action in form_actions:
                if action:
                    normalized = urljoin(base_url, action)
                    urls.add(normalized)

            # Extract from JavaScript onclick handlers (basic)
            onclick_urls = await page.evaluate('''() => {
                const urlPattern = /(https?:\\/\\/[^\\s'"]+)/g;
                const onclickElements = Array.from(document.querySelectorAll('[onclick]'));
                const matches = onclickElements
                    .map(el => el.getAttribute('onclick'))
                    .join(' ')
                    .match(urlPattern) || [];
                return matches;
            }''')

            if onclick_urls:
                for url in onclick_urls:
                    urls.add(url)

        except Exception as e:
            logger.warning(f"Failed to extract URLs from {base_url}: {e}")

        # Remove fragments and normalize
        normalized_urls = {self._normalize_url(url) for url in urls if url}

        return normalized_urls

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL (remove fragments, standardize format)

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        try:
            parsed = urlparse(url)
            # Remove fragment
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized
        except Exception:
            return url

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs are from the same domain

        Args:
            url1: First URL
            url2: Second URL

        Returns:
            True if same domain, False otherwise
        """
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except Exception:
            return False
