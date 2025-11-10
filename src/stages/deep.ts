/**
 * Deep discovery stage - web crawling and endpoint discovery
 * Uses katana for crawling discovered services
 */

import { ToolRunner } from '../tools/runner.js';
import { KatanaParser } from '../tools/parsers.js';
import { logger, logStage } from '../utils/logger.js';
import type { DiscoveryConfig } from '../config.js';
import type { Service, DiscoveredURL, URLDiscoveryResult } from '../models/index.js';
import { URLDiscoveryResultHelper } from '../models/url.js';

/**
 * Results from deep discovery stage
 */
export interface DeepResults {
  urls: URLDiscoveryResult[];
  totalUrls: number;
  totalEndpoints: number;
  totalForms: number;
}

/**
 * Deep discovery stage - web crawling and endpoint discovery
 */
export class DeepDiscovery {
  private config: DiscoveryConfig;
  private runner: ToolRunner;

  /**
   * Create deep discovery stage
   * @param config - Discovery configuration
   */
  constructor(config: DiscoveryConfig) {
    this.config = config;
    this.runner = new ToolRunner(config.katanaTimeout);
  }

  /**
   * Execute deep discovery stage
   * @param services - List of discovered services to crawl
   * @returns Deep discovery results
   */
  async run(services: Service[]): Promise<DeepResults> {
    logStage('deep', 'start', { totalServices: services.length });

    const results: DeepResults = {
      urls: [],
      totalUrls: 0,
      totalEndpoints: 0,
      totalForms: 0,
    };

    if (services.length === 0) {
      logger.warn('No services to crawl - skipping deep discovery');
      return results;
    }

    try {
      // Crawl each service
      const targets = services.map((s) => s.url);
      const urlResults = await this.crawlServices(targets);

      results.urls = urlResults;
      results.totalUrls = urlResults.reduce((sum, r) => sum + r.urls.length, 0);
      results.totalEndpoints = urlResults.reduce(
        (sum, r) => sum + URLDiscoveryResultHelper.getUniqueEndpoints(r).length,
        0
      );
      results.totalForms = urlResults.reduce((sum, r) => sum + r.forms.length, 0);

      logger.info(
        `Deep discovery complete: ${results.totalUrls} URLs, ` +
          `${results.totalEndpoints} endpoints, ${results.totalForms} forms`
      );

      logStage('deep', 'complete', {
        urls: results.totalUrls,
        endpoints: results.totalEndpoints,
        forms: results.totalForms,
      });

      return results;
    } catch (error) {
      logStage('deep', 'error', { error: String(error) });
      throw error;
    }
  }

  /**
   * Crawl services using katana
   */
  private async crawlServices(targets: string[]): Promise<URLDiscoveryResult[]> {
    logger.debug(`Crawling ${targets.length} services with katana`);

    try {
      // Run katana with configured depth
      const depth = this.getDepthConfig();
      const output = await this.runner.runKatana(
        targets,
        depth,
        true, // JS crawling
        this.config.katanaTimeout
      );

      // Parse katana output
      const parsedUrls = KatanaParser.parse(output);
      logger.debug(`Discovered ${parsedUrls.length} URLs from katana`);

      // Group URLs by target
      const urlsByTarget = new Map<string, DiscoveredURL[]>();

      for (const urlData of parsedUrls) {
        try {
          const url = new URL(urlData.url);
          const targetUrl = `${url.protocol}//${url.host}`;

          if (!urlsByTarget.has(targetUrl)) {
            urlsByTarget.set(targetUrl, []);
          }

          urlsByTarget.get(targetUrl).push({
            url: urlData.url,
            method: urlData.method ?? 'GET',
            parameters: this.extractParameters(urlData.url),
            discoveredAt: new Date(),
            source: urlData.source,
          });
        } catch (error) {
          logger.debug(`Failed to parse URL: ${urlData.url}`);
        }
      }

      // Create URLDiscoveryResult for each target
      const results: URLDiscoveryResult[] = [];

      for (const [targetUrl, urls] of urlsByTarget.entries()) {
        results.push({
          targetUrl,
          urls,
          forms: [], // Forms would be extracted from Playwright crawling
          totalUrls: urls.length,
          crawlDepth: depth,
        });
      }

      return results;
    } catch (error) {
      logger.error(`katana execution failed: ${String(error)}`);
      throw error;
    }
  }

  /**
   * Get crawl depth based on configuration
   */
  private getDepthConfig(): number {
    switch (this.config.depth) {
      case 'shallow':
        return 2;
      case 'normal':
        return 3;
      case 'deep':
        return 5;
      default:
        return 3;
    }
  }

  /**
   * Extract query parameters from URL
   */
  private extractParameters(urlString: string): string[] {
    try {
      const url = new URL(urlString);
      return Array.from(url.searchParams.keys());
    } catch {
      return [];
    }
  }
}
