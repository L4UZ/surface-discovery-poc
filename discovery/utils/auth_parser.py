"""Authentication configuration parser"""
import yaml
import os
import re
import logging
from typing import Optional, Dict
from pathlib import Path

from ..models import AuthenticationConfig, AuthConfig

logger = logging.getLogger(__name__)


class AuthConfigParser:
    """Parse and process authentication configuration from YAML"""

    def __init__(self, config_path: str):
        """
        Args:
            config_path: Path to YAML authentication config file
        """
        self.config_path = Path(config_path)
        self.config: Optional[AuthenticationConfig] = None

    def load(self) -> AuthenticationConfig:
        """Load and parse authentication configuration

        Returns:
            AuthenticationConfig object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Auth config not found: {self.config_path}")

        logger.info(f"Loading auth config from {self.config_path}")

        try:
            with open(self.config_path, 'r') as f:
                raw_config = yaml.safe_load(f)

            # Parse with Pydantic model
            self.config = AuthenticationConfig(**raw_config)

            # Substitute environment variables in all auth configs
            for auth_config in self.config.authentication:
                self._substitute_env_vars(auth_config)

            logger.info(f"Loaded {len(self.config.authentication)} auth configurations")
            return self.config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in auth config: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse auth config: {e}")

    def _substitute_env_vars(self, auth_config: AuthConfig):
        """Substitute environment variables in auth config

        Supports both ${VAR} and %{VAR} syntax

        Args:
            auth_config: AuthConfig to process (modified in-place)
        """
        # Substitute in headers
        if auth_config.headers:
            auth_config.headers = self._substitute_dict(auth_config.headers)

        # Substitute in cookies
        if auth_config.cookies:
            auth_config.cookies = self._substitute_dict(auth_config.cookies)

        # Substitute in basic auth
        if auth_config.basic:
            if auth_config.basic.username:
                auth_config.basic.username = self._substitute_string(auth_config.basic.username)
            if auth_config.basic.password:
                auth_config.basic.password = self._substitute_string(auth_config.basic.password)

    def _substitute_dict(self, data: Dict[str, str]) -> Dict[str, str]:
        """Substitute environment variables in dictionary values

        Args:
            data: Dictionary with potentially templated values

        Returns:
            Dictionary with substituted values
        """
        result = {}
        for key, value in data.items():
            result[key] = self._substitute_string(value)
        return result

    def _substitute_string(self, value: str) -> str:
        """Substitute environment variables in string

        Supports:
        - ${VAR_NAME} - standard shell syntax
        - %{VAR_NAME} - alternate syntax

        Args:
            value: String with potential variable references

        Returns:
            String with substituted values

        Raises:
            ValueError: If referenced environment variable doesn't exist
        """
        if not value:
            return value

        # Pattern matches ${VAR} or %{VAR}
        pattern = r'[$%]\{([^}]+)\}'

        def replacer(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)

            if env_value is None:
                raise ValueError(
                    f"Environment variable '{var_name}' not found. "
                    f"Set it before running with --auth-mode."
                )

            return env_value

        try:
            return re.sub(pattern, replacer, value)
        except ValueError:
            raise

    def get_auth_for_url(self, url: str) -> Optional[AuthConfig]:
        """Get authentication config for a specific URL

        Args:
            url: Target URL to find auth config for

        Returns:
            AuthConfig if found, None otherwise
        """
        if not self.config:
            return None

        # Exact match first
        for auth in self.config.authentication:
            if auth.url == url:
                return auth

        # Try domain matching (https://example.com matches https://example.com/path)
        for auth in self.config.authentication:
            if url.startswith(auth.url):
                return auth

        return None

    def to_katana_headers(self, auth_config: AuthConfig) -> Dict[str, str]:
        """Convert AuthConfig to katana-compatible headers

        Combines headers, cookies, and basic auth into header dict

        Args:
            auth_config: Authentication configuration

        Returns:
            Dictionary of headers for katana
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
