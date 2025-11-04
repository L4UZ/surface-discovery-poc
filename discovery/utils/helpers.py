"""Helper utility functions"""
import re
from urllib.parse import urlparse
from typing import Optional
import tldextract


def extract_domain(url: str) -> str:
    """Extract root domain from URL

    Args:
        url: Target URL (http://sub.example.com or example.com)

    Returns:
        Root domain (example.com)
    """
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    parsed = urlparse(url)
    hostname = parsed.netloc or parsed.path

    # Extract domain parts
    extracted = tldextract.extract(hostname)

    if not extracted.domain:
        raise ValueError(f"Could not extract domain from: {url}")

    # Return domain.suffix (e.g., example.com)
    return f"{extracted.domain}.{extracted.suffix}"


def is_subdomain(hostname: str, root_domain: str) -> bool:
    """Check if hostname is a subdomain of root_domain

    Args:
        hostname: Hostname to check (api.example.com)
        root_domain: Root domain (example.com)

    Returns:
        True if hostname is subdomain of root_domain
    """
    return hostname.endswith(f'.{root_domain}') or hostname == root_domain


def normalize_url(url: str) -> str:
    """Normalize URL to standard format

    Args:
        url: URL to normalize

    Returns:
        Normalized URL with scheme and no trailing slash
    """
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    # Remove trailing slash
    if normalized.endswith('/') and parsed.path != '/':
        normalized = normalized[:-1]

    return normalized


def is_valid_domain(domain: str) -> bool:
    """Check if string is a valid domain name

    Args:
        domain: Domain to validate

    Returns:
        True if valid domain format
    """
    # Basic domain regex
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def is_valid_ip(ip: str) -> bool:
    """Check if string is a valid IP address

    Args:
        ip: IP address to validate

    Returns:
        True if valid IPv4 or IPv6
    """
    # IPv4
    ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if re.match(ipv4_pattern, ip):
        return True

    # IPv6 (simplified)
    ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    return bool(re.match(ipv6_pattern, ip))


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    return sanitized or 'output'
