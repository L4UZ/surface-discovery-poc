/**
 * Helper utility functions for domain and URL manipulation
 */

import { parse as parseUrl } from 'url';
import { parse as tldtsParse } from 'tldts';

/**
 * Extract root domain from URL
 * @param url - Target URL (http://sub.example.com or example.com)
 * @returns Root domain (example.com)
 * @throws Error if domain cannot be extracted
 */
export function extractDomain(url: string): string {
  // Add scheme if missing
  let normalizedUrl = url;
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    normalizedUrl = `https://${url}`;
  }

  const parsed = new URL(normalizedUrl);
  const hostname = parsed.hostname || parsed.pathname || '';

  // Extract domain parts using tldts
  const result = tldtsParse(hostname);

  if (!result.domain || !result.publicSuffix) {
    throw new Error(`Could not extract domain from: ${url}`);
  }

  // Return the domain (tldts already includes the public suffix)
  return result.domain;
}

/**
 * Check if hostname is a subdomain of root_domain
 * @param hostname - Hostname to check (api.example.com)
 * @param rootDomain - Root domain (example.com)
 * @returns True if hostname is subdomain of rootDomain
 */
export function isSubdomain(hostname: string, rootDomain: string): boolean {
  return hostname.endsWith(`.${rootDomain}`) || hostname === rootDomain;
}

/**
 * Normalize URL to standard format
 * @param url - URL to normalize
 * @returns Normalized URL with scheme and no trailing slash
 */
export function normalizeUrl(url: string): string {
  // Add scheme if missing
  let normalizedUrl = url;
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    normalizedUrl = `https://${url}`;
  }

  const parsed = parseUrl(normalizedUrl);
  const scheme = parsed.protocol || 'https:';
  const hostname = parsed.hostname || '';
  const path = parsed.pathname || '';

  let normalized = `${scheme}//${hostname}${path}`;

  // Remove trailing slash (except for root path)
  if (normalized.endsWith('/') && path !== '/') {
    normalized = normalized.slice(0, -1);
  }

  return normalized;
}

/**
 * Check if string is a valid domain name
 * @param domain - Domain to validate
 * @returns True if valid domain format
 */
export function isValidDomain(domain: string): boolean {
  // Basic domain regex
  const pattern = /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
  return pattern.test(domain);
}

/**
 * Check if string is a valid IP address
 * @param ip - IP address to validate
 * @returns True if valid IPv4 or IPv6
 */
export function isValidIp(ip: string): boolean {
  // IPv4 pattern
  const ipv4Pattern =
    /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  if (ipv4Pattern.test(ip)) {
    return true;
  }

  // IPv6 pattern (simplified)
  const ipv6Pattern = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
  return ipv6Pattern.test(ip);
}

/**
 * Sanitize filename by removing invalid characters
 * @param filename - Filename to sanitize
 * @returns Sanitized filename
 */
export function sanitizeFilename(filename: string): string {
  // Remove invalid characters
  let sanitized = filename.replace(/[<>:"/\\|?*]/g, '_');

  // Remove leading/trailing spaces and dots
  sanitized = sanitized.replace(/^[\s.]+|[\s.]+$/g, '');

  return sanitized || 'output';
}

/**
 * Generate a unique scan ID with timestamp
 * @returns Unique scan ID (e.g., scan_20250107_123456_abc123)
 */
export function generateScanId(): string {
  const now = new Date();
  const timestamp = now.toISOString().replace(/[-:]/g, '').replace('T', '_').split('.')[0];
  const random = Math.random().toString(36).substring(2, 8);
  return `scan_${timestamp}_${random}`;
}

/**
 * Format duration in milliseconds to human-readable string
 * @param ms - Duration in milliseconds
 * @returns Formatted duration string (e.g., "1m 30s", "45s")
 */
export function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    const remainingMinutes = minutes % 60;
    const remainingSeconds = seconds % 60;
    return `${hours}h ${remainingMinutes}m ${remainingSeconds}s`;
  } else if (minutes > 0) {
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Create a delay promise for async operations
 * @param ms - Milliseconds to delay
 * @returns Promise that resolves after delay
 */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Detect cloud provider from IP or hostname
 * @param ip - IP address
 * @param hostname - Hostname
 * @returns Cloud provider name or undefined
 */
export function getCloudProvider(_ip: string, hostname?: string): string | undefined {
  // AWS detection
  if (hostname?.includes('amazonaws.com') || hostname?.includes('aws.amazon.com')) {
    return 'AWS';
  }

  // Google Cloud detection
  if (
    hostname?.includes('googleusercontent.com') ||
    hostname?.includes('googleapis.com') ||
    hostname?.includes('gcp.google.com')
  ) {
    return 'Google Cloud';
  }

  // Azure detection
  if (
    hostname?.includes('azure.com') ||
    hostname?.includes('azurewebsites.net') ||
    hostname?.includes('windows.net')
  ) {
    return 'Azure';
  }

  // DigitalOcean detection
  if (hostname?.includes('digitaloceanspaces.com')) {
    return 'DigitalOcean';
  }

  // Cloudflare detection (workers, pages)
  if (
    hostname?.includes('cloudflare.com') ||
    hostname?.includes('workers.dev') ||
    hostname?.includes('pages.dev')
  ) {
    return 'Cloudflare';
  }

  return undefined;
}

/**
 * Detect CDN provider from headers or hostname
 * @param hostname - Hostname
 * @param headers - HTTP response headers
 * @returns CDN provider name or undefined
 */
export function getCdnProvider(
  hostname: string,
  headers?: Record<string, string>
): string | undefined {
  // Cloudflare detection
  if (headers?.['cf-ray'] || headers?.['server']?.toLowerCase().includes('cloudflare')) {
    return 'Cloudflare';
  }

  // Fastly detection
  if (headers?.['x-served-by']?.includes('cache') || headers?.['x-fastly-request-id']) {
    return 'Fastly';
  }

  // Akamai detection
  if (
    headers?.['x-akamai-transformed'] ||
    headers?.['server']?.toLowerCase().includes('akamaighost')
  ) {
    return 'Akamai';
  }

  // CloudFront detection
  if (
    headers?.['x-amz-cf-id'] ||
    headers?.['via']?.toLowerCase().includes('cloudfront') ||
    hostname.includes('cloudfront.net')
  ) {
    return 'CloudFront';
  }

  // Incapsula detection
  if (headers?.['x-iinfo'] || headers?.['x-cdn']?.toLowerCase().includes('incapsula')) {
    return 'Incapsula';
  }

  return undefined;
}
