import { describe, it, expect } from 'vitest';
import { extractDomain } from '../src/utils/helpers';

describe('extractDomain', () => {
  describe('URLs with http/https schemes', () => {
    it('should extract domain from URL with https scheme', () => {
      expect(extractDomain('https://example.com')).toBe('example.com');
    });

    it('should extract domain from URL with http scheme', () => {
      expect(extractDomain('http://example.com')).toBe('example.com');
    });

    it('should extract domain from URL with path', () => {
      expect(extractDomain('https://example.com/path/to/page')).toBe('example.com');
    });

    it('should extract domain from URL with query params', () => {
      expect(extractDomain('https://example.com?param=value')).toBe('example.com');
    });

    it('should extract domain from URL with hash', () => {
      expect(extractDomain('https://example.com#section')).toBe('example.com');
    });
  });

  describe('URLs without schemes', () => {
    it('should extract domain from bare domain', () => {
      expect(extractDomain('example.com')).toBe('example.com');
    });

    it('should extract domain from bare domain with path', () => {
      expect(extractDomain('example.com/path')).toBe('example.com');
    });

    it('should extract domain from bare domain with query', () => {
      expect(extractDomain('example.com?query=value')).toBe('example.com');
    });
  });

  describe('Subdomains', () => {
    it('should extract root domain from single subdomain', () => {
      expect(extractDomain('https://www.example.com')).toBe('example.com');
    });

    it('should extract root domain from multiple subdomains', () => {
      expect(extractDomain('https://api.v2.example.com')).toBe('example.com');
    });

    it('should extract root domain from deep subdomain hierarchy', () => {
      expect(extractDomain('https://test.staging.dev.example.com')).toBe('example.com');
    });

    it('should extract root domain from subdomain without scheme', () => {
      expect(extractDomain('api.example.com')).toBe('example.com');
    });
  });

  describe('Different TLDs', () => {
    it('should handle .org TLD', () => {
      expect(extractDomain('https://example.org')).toBe('example.org');
    });

    it('should handle .net TLD', () => {
      expect(extractDomain('https://example.net')).toBe('example.net');
    });

    it('should handle country code TLDs', () => {
      expect(extractDomain('https://example.co.uk')).toBe('example.co.uk');
    });

    it('should handle .io TLD', () => {
      expect(extractDomain('https://example.io')).toBe('example.io');
    });

    it('should handle .dev TLD', () => {
      expect(extractDomain('https://example.dev')).toBe('example.dev');
    });
  });

  describe('Multi-part TLDs', () => {
    it('should handle .co.uk correctly', () => {
      expect(extractDomain('https://www.example.co.uk')).toBe('example.co.uk');
    });

    it('should handle .com.au correctly', () => {
      expect(extractDomain('https://www.example.com.au')).toBe('example.com.au');
    });

    it('should handle .gov.uk correctly', () => {
      expect(extractDomain('https://service.gov.uk')).toBe('service.gov.uk');
    });

    it('should handle .co.jp correctly', () => {
      expect(extractDomain('https://www.example.co.jp')).toBe('example.co.jp');
    });
  });

  describe('Edge cases', () => {
    it('should handle localhost', () => {
      expect(() => extractDomain('localhost')).toThrow('Could not extract domain');
    });

    it('should handle IP addresses', () => {
      expect(() => extractDomain('192.168.1.1')).toThrow('Could not extract domain');
    });

    it('should handle URLs with port numbers', () => {
      expect(extractDomain('https://example.com:8080')).toBe('example.com');
    });

    it('should handle URLs with authentication', () => {
      expect(extractDomain('https://user:pass@example.com')).toBe('example.com');
    });

    it('should handle URLs with all components', () => {
      expect(extractDomain('https://user:pass@www.example.com:8080/path?query=1#hash')).toBe(
        'example.com'
      );
    });
  });

  describe('Error cases', () => {
    it('should throw error for invalid URL', () => {
      expect(() => extractDomain('not-a-valid-url')).toThrow('Could not extract domain');
    });

    it('should throw error for empty string', () => {
      expect(() => extractDomain('')).toThrow();
    });

    it('should throw error for URL with no valid domain', () => {
      expect(() => extractDomain('https://')).toThrow();
    });

    it('should throw error for invalid characters', () => {
      expect(() => extractDomain('https://exam ple.com')).toThrow();
    });
  });

  describe('Real-world examples', () => {
    it('should extract from GitHub URL', () => {
      expect(extractDomain('https://github.com/user/repo')).toBe('github.com');
    });

    it('should extract from Google subdomain', () => {
      expect(extractDomain('https://mail.google.com')).toBe('google.com');
    });

    it('should extract from AWS service URL', () => {
      expect(extractDomain('https://s3.amazonaws.com')).toBe('amazonaws.com');
    });

    it('should extract from Cloudflare Pages', () => {
      expect(extractDomain('https://myproject.pages.dev')).toBe('pages.dev');
    });

    it('should extract from CDN URL', () => {
      expect(extractDomain('https://cdn.jsdelivr.net/npm/package')).toBe('jsdelivr.net');
    });
  });
});
