"""Authenticated discovery stage - deep crawling with authentication"""
import logging
import json
import re
from typing import List, Optional, Dict, Set
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from pydantic import BaseModel, Field

from ..config import DiscoveryConfig
from ..models import Service, Endpoint, AuthConfig
from ..tools.runner import ToolRunner

logger = logging.getLogger(__name__)


class PathParameter(BaseModel):
    """Extracted path parameter"""
    name: str = Field(..., description="Parameter name")
    pattern: str = Field(..., description="Regex pattern that matched")
    example_values: List[str] = Field(default_factory=list, description="Observed values")
    position: int = Field(..., description="Position in path (0-indexed)")


class AuthenticatedResults(BaseModel):
    """Results from authenticated discovery stage"""
    endpoints: List[Endpoint] = Field(default_factory=list)
    path_parameters: List[PathParameter] = Field(default_factory=list)
    total_endpoints: int = 0
    authenticated_endpoints: int = 0
    unique_paths: Set[str] = Field(default_factory=set)

    class Config:
        arbitrary_types_allowed = True


class AuthenticatedDiscovery:
    """Authenticated discovery stage - crawl authenticated surfaces"""

    # Common path parameter patterns
    PATH_PARAM_PATTERNS = [
        # UUID patterns
        (r'/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:/|$)', 'uuid'),
        # Numeric IDs
        (r'/(\d+)(?:/|$)', 'id'),
        # Alphanumeric slugs
        (r'/([a-z0-9\-_]+)(?:/|$)', 'slug'),
        # Email-like
        (r'/([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})(?:/|$)', 'email'),
        # Hex strings
        (r'/([a-f0-9]{32,})(?:/|$)', 'hash'),
        # Date patterns (YYYY-MM-DD)
        (r'/(\d{4}-\d{2}-\d{2})(?:/|$)', 'date'),
    ]

    def __init__(self, config: DiscoveryConfig):
        """Initialize authenticated discovery

        Args:
            config: Discovery configuration
        """
        self.config = config
        self.runner = ToolRunner(timeout=config.katana_timeout if hasattr(config, 'katana_timeout') else 300)

    async def run(
        self,
        target_url: str,
        auth_config: AuthConfig
    ) -> AuthenticatedResults:
        """Execute authenticated discovery

        Args:
            target_url: Target URL requiring authentication
            auth_config: Authentication configuration

        Returns:
            AuthenticatedResults with discovered endpoints and parameters
        """
        logger.info(f"Starting authenticated discovery for {target_url}")
        results = AuthenticatedResults()

        try:
            # Phase 1: Authenticated crawling with katana
            endpoints = await self._crawl_authenticated(target_url, auth_config)
            results.endpoints = endpoints
            results.total_endpoints = len(endpoints)
            results.authenticated_endpoints = len([ep for ep in endpoints if ep.requires_auth])

            # Phase 2: Extract path parameters
            path_params = self._extract_path_parameters(endpoints)
            results.path_parameters = path_params

            # Calculate unique paths
            results.unique_paths = {self._extract_path(ep.url) for ep in endpoints}

            logger.info(
                f"Authenticated discovery complete: {results.total_endpoints} endpoints, "
                f"{len(results.path_parameters)} path parameters, "
                f"{len(results.unique_paths)} unique paths"
            )

        except Exception as e:
            logger.error(f"Authenticated discovery failed: {e}")
            raise

        return results

    async def _crawl_authenticated(
        self,
        target_url: str,
        auth_config: AuthConfig
    ) -> List[Endpoint]:
        """Crawl authenticated surface with katana

        Args:
            target_url: Target URL to crawl
            auth_config: Authentication configuration

        Returns:
            List of discovered endpoints
        """
        logger.debug(f"Crawling {target_url} with authentication")
        endpoints = []
        seen_urls = set()

        try:
            # Build katana headers from auth config
            headers = self._build_katana_headers(auth_config)

            # Run katana with authentication headers
            output = await self.runner.run_katana_authenticated(
                targets=[target_url],
                headers=headers,
                depth=3,  # Deeper crawl for authenticated surfaces
                js_crawl=True,
                timeout=self.config.katana_timeout if hasattr(self.config, 'katana_timeout') else 300
            )

            # Parse JSONL output
            for line in output.strip().split('\n'):
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    endpoint = self._parse_katana_result(data, requires_auth=True)

                    if endpoint and endpoint.url not in seen_urls:
                        endpoints.append(endpoint)
                        seen_urls.add(endpoint.url)

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse katana JSON: {e}")
                    continue

            logger.debug(f"Discovered {len(endpoints)} authenticated endpoints")

        except Exception as e:
            logger.error(f"Authenticated crawling failed: {e}")
            raise

        return endpoints

    def _build_katana_headers(self, auth_config: AuthConfig) -> Dict[str, str]:
        """Build headers for katana from auth config

        Args:
            auth_config: Authentication configuration

        Returns:
            Dictionary of headers
        """
        headers = {}

        # Add custom headers
        if auth_config.headers:
            headers.update(auth_config.headers)

        # Add cookies as Cookie header
        if auth_config.cookies:
            cookie_parts = [f"{k}={v}" for k, v in auth_config.cookies.items()]
            headers['Cookie'] = '; '.join(cookie_parts)

        # Add basic auth as Authorization header
        if auth_config.basic:
            import base64
            credentials = f"{auth_config.basic.username}:{auth_config.basic.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f"Basic {encoded}"

        return headers

    def _parse_katana_result(self, data: Dict, requires_auth: bool = False) -> Optional[Endpoint]:
        """Parse katana JSON result into Endpoint

        Args:
            data: Katana JSON result
            requires_auth: Whether this endpoint requires authentication

        Returns:
            Endpoint object or None
        """
        try:
            request = data.get('request', {})
            response = data.get('response', {})

            method = request.get('method', 'GET')
            url = request.get('endpoint')

            if not url:
                return None

            status_code = response.get('status_code')

            # Extract URL parameters
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            parameters = list(query_params.keys())

            # Determine discovery source
            discovered_via = 'auth_crawl'
            if data.get('source') == 'javascript':
                discovered_via = 'auth_js_analysis'

            endpoint = Endpoint(
                url=url,
                method=method,
                status_code=status_code,
                discovered_via=discovered_via,
                parameters=parameters,
                requires_auth=requires_auth
            )

            return endpoint

        except Exception as e:
            logger.warning(f"Failed to parse katana result: {e}")
            return None

    def _extract_path_parameters(self, endpoints: List[Endpoint]) -> List[PathParameter]:
        """Extract path parameters from endpoints using pattern recognition

        Args:
            endpoints: List of discovered endpoints

        Returns:
            List of identified path parameters
        """
        logger.debug("Extracting path parameters from endpoints")
        path_params: Dict[str, PathParameter] = {}

        for endpoint in endpoints:
            path = urlparse(endpoint.url).path
            segments = [s for s in path.split('/') if s]

            # Check each segment against patterns
            for i, segment in enumerate(segments):
                for pattern, param_type in self.PATH_PARAM_PATTERNS:
                    match = re.search(pattern, '/' + segment + '/')
                    if match:
                        param_value = match.group(1)

                        # Create unique key for this parameter position
                        key = f"{i}:{param_type}"

                        if key not in path_params:
                            path_params[key] = PathParameter(
                                name=param_type,
                                pattern=pattern,
                                example_values=[],
                                position=i
                            )

                        # Add example value if not already present
                        if param_value not in path_params[key].example_values:
                            path_params[key].example_values.append(param_value)

                        break  # Only match first pattern per segment

        result = list(path_params.values())
        logger.debug(f"Extracted {len(result)} path parameters")
        return result

    def _extract_path(self, url: str) -> str:
        """Extract path component from URL

        Args:
            url: Full URL

        Returns:
            Path component without query string
        """
        parsed = urlparse(url)
        return parsed.path
