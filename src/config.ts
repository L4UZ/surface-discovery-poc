/**
 * Configuration management for discovery service
 */

import { z } from 'zod';

/**
 * Discovery configuration schema
 */
export const discoveryConfigSchema = z
  .object({
    // Execution settings
    /** Discovery depth: shallow|normal|deep */
    depth: z.enum(['shallow', 'normal', 'deep']).default('normal'),
    /** Max execution time in seconds */
    timeout: z.number().int().positive().default(600),
    /** Max parallel tasks */
    parallel: z.number().int().positive().default(10),

    // Tool timeouts (seconds)
    /** Subfinder execution timeout */
    subfinderTimeout: z.number().int().positive().default(180),
    /** DNSx execution timeout */
    dnsxTimeout: z.number().int().positive().default(120),
    /** HTTPx execution timeout */
    httpxTimeout: z.number().int().positive().default(180),
    /** Katana execution timeout */
    katanaTimeout: z.number().int().positive().default(120),
    /** Naabu execution timeout */
    naabuTimeout: z.number().int().positive().default(120),

    // Port scanning settings
    /** Packets per second for port scanning */
    portScanRate: z.number().int().positive().default(1000),

    // Discovery limits
    /** Max subdomains to process (null = unlimited) */
    maxSubdomains: z.number().int().positive().optional(),
    /** Max services to crawl deeply */
    maxCrawlServices: z.number().int().positive().default(10),
    /** Web crawling depth */
    crawlDepth: z.number().int().positive().default(3),

    // Deep URL Discovery (Playwright)
    /** Maximum depth for deep crawler */
    maxCrawlDepth: z.number().int().positive().default(3),
    /** Max URLs per domain */
    maxUrlsPerDomain: z.number().int().positive().default(500),
    /** Enable form submission and interaction */
    formInteraction: z.boolean().default(false),
    /** Enable JavaScript execution with Playwright */
    javascriptExecution: z.boolean().default(false),
    /** Deep crawl timeout in seconds */
    crawlTimeout: z.number().int().positive().default(600),

    // Rate limiting
    /** HTTP requests per second */
    httpRateLimit: z.number().int().positive().default(50),
    /** DNS queries per second */
    dnsRateLimit: z.number().int().positive().default(100),

    // Output settings
    /** Enable verbose logging */
    verbose: z.boolean().default(false),
  })
  .strict()
  .readonly();

export type DiscoveryConfig = z.infer<typeof discoveryConfigSchema>;

/**
 * Discovery depth type
 */
export type DiscoveryDepth = 'shallow' | 'normal' | 'deep';

/**
 * Depth presets for different discovery scenarios
 */
export const DEPTH_CONFIGS: Record<string, DiscoveryConfig> = {
  shallow: Object.freeze({
    depth: 'shallow',
    timeout: 300,
    parallel: 5,
    subfinderTimeout: 60,
    dnsxTimeout: 60,
    httpxTimeout: 90,
    katanaTimeout: 60,
    naabuTimeout: 90,
    portScanRate: 1000,
    maxSubdomains: 20,
    maxCrawlServices: 3,
    crawlDepth: 2,
    maxCrawlDepth: 2,
    maxUrlsPerDomain: 100,
    formInteraction: false,
    javascriptExecution: false,
    crawlTimeout: 300,
    httpRateLimit: 50,
    dnsRateLimit: 100,
    verbose: false,
  } as const),

  normal: Object.freeze({
    depth: 'normal',
    timeout: 600,
    parallel: 10,
    subfinderTimeout: 180,
    dnsxTimeout: 120,
    httpxTimeout: 180,
    katanaTimeout: 120,
    naabuTimeout: 180,
    portScanRate: 1500,
    maxSubdomains: undefined,
    maxCrawlServices: 10,
    crawlDepth: 3,
    maxCrawlDepth: 3,
    maxUrlsPerDomain: 500,
    formInteraction: false,
    javascriptExecution: false,
    crawlTimeout: 600,
    httpRateLimit: 50,
    dnsRateLimit: 100,
    verbose: false,
  } as const),

  deep: Object.freeze({
    depth: 'deep',
    timeout: 900,
    parallel: 15,
    subfinderTimeout: 300,
    dnsxTimeout: 180,
    httpxTimeout: 300,
    katanaTimeout: 300,
    naabuTimeout: 900,
    portScanRate: 2000,
    maxSubdomains: undefined,
    maxCrawlServices: 20,
    crawlDepth: 5,
    maxCrawlDepth: 5,
    maxUrlsPerDomain: 2000,
    formInteraction: true,
    javascriptExecution: true,
    crawlTimeout: 1200,
    httpRateLimit: 50,
    dnsRateLimit: 100,
    verbose: false,
  } as const),
};

/**
 * Get configuration with optional overrides
 * @param depth - Discovery depth preset
 * @param overrides - Configuration overrides
 * @returns Validated discovery configuration
 */
export function getConfig(
  depth: DiscoveryDepth = 'normal',
  overrides?: Partial<DiscoveryConfig>
): DiscoveryConfig {
  const baseConfig = DEPTH_CONFIGS[depth] || DEPTH_CONFIGS.normal;

  if (overrides && Object.keys(overrides).length > 0) {
    const mergedConfig = {
      ...baseConfig,
      ...overrides,
    };
    return discoveryConfigSchema.parse(mergedConfig);
  }

  return baseConfig as DiscoveryConfig;
}
