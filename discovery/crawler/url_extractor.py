"""URL extraction and normalization utilities for deep discovery"""
import logging
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.async_api import Page

logger = logging.getLogger(__name__)


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

        try:
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

            # Extract from JavaScript onclick handlers (basic pattern matching)
            onclick_urls = await page.evaluate('''() => {
                const urlPattern = /(https?:\\/\\/[^\\s'"]+)/g;
                return Array.from(document.querySelectorAll('[onclick]'))
                    .map(el => el.getAttribute('onclick'))
                    .join(' ')
                    .match(urlPattern) || [];
            }''')
            if onclick_urls:
                urls.update(onclick_urls)

            # Extract from meta refresh tags
            meta_refresh = await page.evaluate('''() => {
                const meta = document.querySelector('meta[http-equiv="refresh"]');
                if (!meta) return null;
                const content = meta.getAttribute('content');
                if (!content) return null;
                const match = content.match(/url=(.+)/i);
                return match ? match[1] : null;
            }''')
            if meta_refresh:
                urls.add(meta_refresh)

            # Extract from iframe sources
            iframe_sources = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('iframe[src]'))
                    .map(iframe => iframe.src);
            }''')
            urls.update(iframe_sources)

        except Exception as e:
            logger.warning(f"Failed to extract URLs from {base_url}: {e}")

        # Normalize all URLs
        normalized = {URLExtractor.normalize_url(url, base_url) for url in urls if url}

        return normalized

    @staticmethod
    async def extract_forms(page: Page) -> List[Dict]:
        """
        Discover forms and their POST endpoints

        Returns:
            List of form metadata dictionaries with action, method, and fields
        """
        try:
            forms = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('form')).map(form => ({
                    action: form.action,
                    method: form.method || 'GET',
                    fields: Array.from(form.querySelectorAll('input, select, textarea'))
                        .map(field => ({
                            name: field.name,
                            type: field.type || field.tagName.toLowerCase(),
                            required: field.required,
                            id: field.id || null
                        }))
                }));
            }''')

            logger.debug(f"Extracted {len(forms)} forms from page")
            return forms

        except Exception as e:
            logger.warning(f"Failed to extract forms: {e}")
            return []

    @staticmethod
    async def extract_api_endpoints(page: Page) -> Set[str]:
        """
        Extract potential API endpoints from JavaScript code

        Returns:
            Set of discovered API endpoint patterns
        """
        api_endpoints = set()

        try:
            # Extract from fetch/axios calls in page scripts
            endpoints = await page.evaluate('''() => {
                const apiPattern = /(['"\`])(\\/)(?:api|v\\d+|graphql|rest)([^'"\`]*?)\\1/g;
                const scripts = Array.from(document.querySelectorAll('script'));
                const endpoints = new Set();

                scripts.forEach(script => {
                    const content = script.textContent || '';
                    let match;
                    while ((match = apiPattern.exec(content)) !== null) {
                        endpoints.add(match[2] + match[3]);
                    }
                });

                return Array.from(endpoints);
            }''')

            api_endpoints.update(endpoints)
            logger.debug(f"Extracted {len(api_endpoints)} potential API endpoints")

        except Exception as e:
            logger.warning(f"Failed to extract API endpoints: {e}")

        return api_endpoints

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
        try:
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

        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {e}")
            return url

    @staticmethod
    def is_same_domain(url1: str, url2: str) -> bool:
        """
        Check if two URLs belong to the same domain

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

    @staticmethod
    def extract_path(url: str) -> str:
        """
        Extract path component from URL

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

    @staticmethod
    def is_valid_http_url(url: str) -> bool:
        """
        Check if URL is a valid HTTP/HTTPS URL

        Args:
            url: URL to validate

        Returns:
            True if valid HTTP/HTTPS URL, False otherwise
        """
        try:
            parsed = urlparse(url)
            return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
        except Exception:
            return False
