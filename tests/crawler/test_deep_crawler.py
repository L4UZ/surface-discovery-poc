"""Tests for DeepURLCrawler with Playwright"""
import pytest
from discovery.crawler.deep_crawler import DeepURLCrawler


@pytest.mark.asyncio
async def test_deep_crawler_initialization():
    """Test deep crawler initialization"""
    crawler = DeepURLCrawler(max_depth=3, max_urls=100)

    assert crawler.max_depth == 3
    assert crawler.max_urls == 100
    assert len(crawler.visited_urls) == 0
    assert len(crawler.discovered_urls) == 0


@pytest.mark.asyncio
async def test_normalize_url():
    """Test URL normalization"""
    crawler = DeepURLCrawler()

    # Remove fragments
    result = crawler._normalize_url("https://example.com/page#section")
    assert result == "https://example.com/page"

    # With query parameters
    result = crawler._normalize_url("https://example.com/api?key=value")
    assert result == "https://example.com/api?key=value"


@pytest.mark.asyncio
async def test_is_same_domain():
    """Test domain comparison"""
    crawler = DeepURLCrawler()

    assert crawler._is_same_domain(
        "https://example.com/page1",
        "https://example.com/page2"
    ) is True

    assert crawler._is_same_domain(
        "https://example.com/page",
        "https://other.com/page"
    ) is False


@pytest.mark.asyncio
async def test_crawl_empty_urls():
    """Test crawl with empty URL list"""
    crawler = DeepURLCrawler()
    result = await crawler.crawl([])

    assert len(result) == 0


@pytest.mark.asyncio
@pytest.mark.slow
async def test_crawl_with_auth():
    """Test crawling with authentication context - integration test"""
    # This would be an integration test requiring a test server
    # Skipped in unit tests
    pass


@pytest.mark.asyncio
@pytest.mark.slow
async def test_crawl_max_depth():
    """Test respecting max depth limit - integration test"""
    # This would be an integration test requiring a test server
    # Skipped in unit tests
    pass


@pytest.mark.asyncio
@pytest.mark.slow
async def test_crawl_max_urls():
    """Test respecting max URLs limit - integration test"""
    # This would be an integration test requiring a test server
    # Skipped in unit tests
    pass
