"""Basic tests for core components"""
import pytest
from discovery.utils.helpers import extract_domain, is_valid_domain, is_valid_ip
from discovery.config import get_config
from discovery.models import Subdomain, DNSRecords, Service, Technology


class TestHelpers:
    """Test utility helper functions"""

    def test_extract_domain_with_http(self):
        """Test domain extraction from HTTP URL"""
        assert extract_domain("http://www.example.com") == "example.com"

    def test_extract_domain_with_https(self):
        """Test domain extraction from HTTPS URL"""
        assert extract_domain("https://api.example.com/path") == "example.com"

    def test_extract_domain_without_scheme(self):
        """Test domain extraction without scheme"""
        assert extract_domain("example.com") == "example.com"

    def test_extract_subdomain(self):
        """Test subdomain extraction"""
        assert extract_domain("https://api.v2.example.com") == "example.com"

    def test_is_valid_domain_valid(self):
        """Test valid domain validation"""
        assert is_valid_domain("example.com") is True
        assert is_valid_domain("sub.example.com") is True

    def test_is_valid_domain_invalid(self):
        """Test invalid domain validation"""
        assert is_valid_domain("invalid") is False
        assert is_valid_domain("") is False

    def test_is_valid_ip_ipv4(self):
        """Test IPv4 validation"""
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("8.8.8.8") is True

    def test_is_valid_ip_invalid(self):
        """Test invalid IP validation"""
        assert is_valid_ip("999.999.999.999") is False
        assert is_valid_ip("not an ip") is False


class TestConfig:
    """Test configuration management"""

    def test_default_config(self):
        """Test default configuration"""
        config = get_config()
        assert config.depth == "normal"
        assert config.timeout == 600

    def test_shallow_config(self):
        """Test shallow depth configuration"""
        config = get_config("shallow")
        assert config.depth == "shallow"
        assert config.timeout == 300
        assert config.max_subdomains == 20

    def test_deep_config(self):
        """Test deep depth configuration"""
        config = get_config("deep")
        assert config.depth == "deep"
        assert config.timeout == 900

    def test_config_overrides(self):
        """Test configuration overrides"""
        config = get_config("normal", timeout=1200, parallel=20)
        assert config.timeout == 1200
        assert config.parallel == 20


class TestModels:
    """Test Pydantic data models"""

    def test_subdomain_creation(self):
        """Test Subdomain model creation"""
        subdomain = Subdomain(
            name="api.example.com",
            ips=["192.168.1.1"],
            discovered_via="passive"
        )
        assert subdomain.name == "api.example.com"
        assert len(subdomain.ips) == 1
        assert subdomain.status == "unknown"

    def test_dns_records_creation(self):
        """Test DNSRecords model creation"""
        dns = DNSRecords(
            a=["192.168.1.1"],
            aaaa=["2001:db8::1"],
            mx=["mail.example.com"]
        )
        assert len(dns.a) == 1
        assert len(dns.aaaa) == 1
        assert len(dns.mx) == 1

    def test_service_creation(self):
        """Test Service model creation"""
        service = Service(
            url="https://example.com",
            status_code=200,
            title="Example Domain"
        )
        assert service.url == "https://example.com"
        assert service.status_code == 200

    def test_technology_creation(self):
        """Test Technology model creation"""
        tech = Technology(
            name="nginx",
            version="1.24.0",
            category="web_server",
            confidence=0.95
        )
        assert tech.name == "nginx"
        assert tech.confidence == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
