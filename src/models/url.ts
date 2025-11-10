/**
 * URL discovery data models for deep crawling with Playwright
 */

import { z } from 'zod';

/**
 * Individual discovered URL from deep crawling
 */
export const discoveredURLSchema = z.object({
  /** Full URL */
  url: z.string().url(),
  /** HTTP method (GET, POST, etc.) */
  method: z.string().default('GET'),
  /** Page where URL was found */
  sourcePage: z.string().url().optional(),
  /** Crawl depth from start */
  depth: z.number().int().nonnegative().default(0),
  /** Query params or form fields */
  parameters: z.record(z.any()).default({}),
  /** Timestamp when URL was discovered */
  discoveredAt: z.date().default(() => new Date()),
  /** HTTP response code */
  responseCode: z.number().int().min(100).max(599).optional(),
  /** Content-Type header */
  contentType: z.string().optional(),
  /** Discovery method: deep_crawl|form|js_analysis */
  discoveredVia: z.string().default('deep_crawl'),
  /** Discovery source (alias for discoveredVia) */
  source: z.string().optional(),
});

export type DiscoveredURL = z.infer<typeof discoveredURLSchema>;

/**
 * Form metadata discovered during crawling
 */
export const formDataSchema = z.object({
  /** Form action URL */
  actionUrl: z.string().url(),
  /** Form submission method */
  method: z.string().default('GET'),
  /** Form fields with metadata */
  fields: z.array(z.record(z.any())).default([]),
  /** Page containing the form */
  sourcePage: z.string().url().optional(),
  /** Whether form requires authentication */
  requiresAuth: z.boolean().optional(),
});

export type FormData = z.infer<typeof formDataSchema>;

/**
 * Results from URL discovery crawl using Playwright
 */
export const urlDiscoveryResultSchema = z.object({
  /** All discovered URLs */
  urls: z.array(discoveredURLSchema).default([]),
  /** Discovered forms */
  forms: z.array(formDataSchema).default([]),
  /** Total URLs discovered */
  totalUrls: z.number().int().nonnegative().default(0),
  /** Unique URLs (deduplicated) */
  uniqueUrls: z.number().int().nonnegative().default(0),
  /** Maximum crawl depth reached */
  crawlDepthReached: z.number().int().nonnegative().default(0),
  /** Crawl depth (alias for crawlDepthReached) */
  crawlDepth: z.number().int().nonnegative().optional(),
  /** Total pages visited during crawl */
  pagesVisited: z.number().int().nonnegative().default(0),
  /** Total forms found */
  formsDiscovered: z.number().int().nonnegative().default(0),
  /** Potential API endpoints discovered */
  apiEndpoints: z.array(z.string()).default([]),
  /** URLs discovered via JavaScript analysis */
  javascriptUrls: z.number().int().nonnegative().default(0),
  /** Target URL for the crawl */
  targetUrl: z.string().optional(),
});

export type URLDiscoveryResult = z.infer<typeof urlDiscoveryResultSchema>;

/**
 * Helper functions for URL discovery results
 */
export class URLDiscoveryResultHelper {
  /**
   * Add a discovered URL to results
   */
  static addUrl(result: URLDiscoveryResult, url: DiscoveredURL): URLDiscoveryResult {
    return {
      ...result,
      urls: [...result.urls, url],
      totalUrls: result.totalUrls + 1,
    };
  }

  /**
   * Add a discovered form to results
   */
  static addForm(result: URLDiscoveryResult, form: FormData): URLDiscoveryResult {
    return {
      ...result,
      forms: [...result.forms, form],
      formsDiscovered: result.formsDiscovered + 1,
    };
  }

  /**
   * Extract unique URL paths from discovered URLs
   */
  static getUniquePaths(result: URLDiscoveryResult): Set<string> {
    return new Set(result.urls.map((url) => new URL(url.url).pathname));
  }

  /**
   * Get URLs discovered at specific depth
   */
  static getUrlsByDepth(result: URLDiscoveryResult, depth: number): DiscoveredURL[] {
    return result.urls.filter((url) => url.depth === depth);
  }

  /**
   * Get all POST endpoints discovered
   */
  static getPostEndpoints(result: URLDiscoveryResult): DiscoveredURL[] {
    return result.urls.filter((url) => url.method === 'POST');
  }

  /**
   * Get forms filtered by HTTP method
   */
  static getFormsByMethod(result: URLDiscoveryResult, method: string): FormData[] {
    return result.forms.filter((form) => form.method.toUpperCase() === method.toUpperCase());
  }

  /**
   * Get unique endpoints (deduplicated URLs)
   */
  static getUniqueEndpoints(result: URLDiscoveryResult): DiscoveredURL[] {
    const seen = new Set<string>();
    return result.urls.filter((url) => {
      if (seen.has(url.url)) {
        return false;
      }
      seen.add(url.url);
      return true;
    });
  }
}
