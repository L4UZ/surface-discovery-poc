"""Tests for URL extraction and normalization utilities"""
import pytest
from discovery.crawler.url_extractor import URLExtractor


def test_normalize_url():
    """Test URL normalization"""
    base = "https://example.com/page"

    # Relative URL
    result = URLExtractor.normalize_url("./other", base)
    assert result == "https://example.com/other"

    # Absolute URL
    result = URLExtractor.normalize_url("https://example.com/test", base)
    assert result == "https://example.com/test"

    # Remove fragment
    result = URLExtractor.normalize_url("https://example.com/page#section", base)
    assert result == "https://example.com/page"

    # With query parameters
    result = URLExtractor.normalize_url("https://example.com/api?key=value", base)
    assert result == "https://example.com/api?key=value"


def test_is_same_domain():
    """Test domain comparison"""
    assert URLExtractor.is_same_domain(
        "https://example.com/page1",
        "https://example.com/page2"
    ) is True

    assert URLExtractor.is_same_domain(
        "https://example.com/page1",
        "https://other.com/page2"
    ) is False

    assert URLExtractor.is_same_domain(
        "http://example.com/page1",
        "https://example.com/page2"
    ) is True  # Same domain, different scheme


def test_extract_path():
    """Test path extraction"""
    assert URLExtractor.extract_path("https://example.com/api/v1/users") == "/api/v1/users"
    assert URLExtractor.extract_path("https://example.com/") == "/"
    assert URLExtractor.extract_path("https://example.com") == "/"
    assert URLExtractor.extract_path("https://example.com/page?param=value") == "/page"


def test_is_valid_http_url():
    """Test URL validation"""
    assert URLExtractor.is_valid_http_url("https://example.com") is True
    assert URLExtractor.is_valid_http_url("http://example.com") is True
    assert URLExtractor.is_valid_http_url("ftp://example.com") is False
    assert URLExtractor.is_valid_http_url("not-a-url") is False
    assert URLExtractor.is_valid_http_url("") is False


@pytest.mark.asyncio
async def test_extract_forms():
    """Test form extraction - placeholder for Playwright integration test"""
    # This would require Playwright page fixture
    # Actual implementation would use a real page object
    pass


@pytest.mark.asyncio
async def test_extract_from_page():
    """Test URL extraction from page - placeholder for Playwright integration test"""
    # This would require Playwright page fixture
    # Actual implementation would use a real page object
    pass


@pytest.mark.asyncio
async def test_extract_api_endpoints():
    """Test API endpoint extraction - placeholder for Playwright integration test"""
    # This would require Playwright page fixture
    # Actual implementation would use a real page object
    pass
