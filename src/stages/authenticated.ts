/**
 * Authenticated discovery stage - crawl authenticated surfaces
 * Uses katana with authentication headers for authenticated endpoint discovery
 */

import { ToolRunner } from '../tools/runner.js';
import { KatanaParser } from '../tools/parsers.js';
import { logger, logStage } from '../utils/logger.js';
import type { DiscoveryConfig } from '../config.js';
import type { AuthenticationConfig, DiscoveredURL, URLDiscoveryResult } from '../models/index.js';
import { URLDiscoveryResultHelper } from '../models/url.js';

/**
 * Results from authenticated discovery stage
 */
export interface AuthenticatedResults {
  urls: URLDiscoveryResult[];
  totalUrls: number;
  totalEndpoints: number;
  authenticatedEndpointsCount: number;
}

/**
 * Authenticated discovery stage - crawl with authentication
 */
export class AuthenticatedDiscovery {
  private config: DiscoveryConfig;
  private runner: ToolRunner;

  constructor(config: DiscoveryConfig) {
    this.config = config;
    this.runner = new ToolRunner(config.katanaTimeout);
  }

  /**
   * Execute authenticated discovery stage
   * @param authConfig - Authentication configuration
   * @returns Authenticated discovery results
   */
  async run(authConfig: AuthenticationConfig): Promise<AuthenticatedResults> {
    logStage('authenticated', 'start', {
      totalTargets: authConfig.targets?.length ?? 0,
    });

    const results: AuthenticatedResults = {
      urls: [],
      totalUrls: 0,
      totalEndpoints: 0,
      authenticatedEndpointsCount: 0,
    };

    const targets = Object.keys(authConfig.targets);

    if (targets.length === 0) {
      logger.warn('No authenticated targets configured');
      return results;
    }

    try {
      // Crawl each authenticated target
      for (const targetUrl of targets) {
        const targetConfig = authConfig.targets[targetUrl];
        const headers = this.buildHeaders(targetConfig);

        logger.info(`Crawling authenticated target: ${targetUrl}`);

        const urlResult = await this.crawlAuthenticated(targetUrl, headers);

        if (urlResult) {
          results.urls.push(urlResult);
          results.totalUrls += urlResult.urls.length;
          results.totalEndpoints += URLDiscoveryResultHelper.getUniqueEndpoints(urlResult).length;
          results.authenticatedEndpointsCount += urlResult.urls.length;
        }
      }

      logger.info(
        `Authenticated discovery complete: ${results.totalUrls} URLs, ` +
          `${results.totalEndpoints} endpoints across ${targets.length} targets`
      );

      logStage('authenticated', 'complete', {
        urls: results.totalUrls,
        endpoints: results.totalEndpoints,
        authenticatedEndpoints: results.authenticatedEndpointsCount,
      });

      return results;
    } catch (error) {
      logStage('authenticated', 'error', { error: String(error) });
      throw error;
    }
  }

  /**
   * Crawl a single authenticated target
   */
  private async crawlAuthenticated(
    targetUrl: string,
    headers: Record<string, string>
  ): Promise<URLDiscoveryResult | null> {
    try {
      // Run katana with authentication headers
      const depth = this.getDepthConfig();
      const output = await this.runner.runKatanaAuthenticated(
        [targetUrl],
        headers,
        depth,
        true, // JS crawling
        this.config.katanaTimeout
      );

      // Parse katana output
      const parsedUrls = KatanaParser.parse(output);
      logger.debug(`Discovered ${parsedUrls.length} authenticated URLs from ${targetUrl}`);

      // Convert to DiscoveredURL objects
      const urls: DiscoveredURL[] = parsedUrls.map((urlData) => ({
        url: urlData.url,
        method: urlData.method ?? 'GET',
        parameters: this.extractParameters(urlData.url),
        discoveredAt: new Date(),
        source: 'authenticated',
        authenticated: true,
      }));

      return {
        targetUrl,
        urls,
        forms: [],
        totalUrls: urls.length,
        crawlDepth: depth,
      };
    } catch (error) {
      logger.error(`Authenticated crawl failed for ${targetUrl}: ${error}`);
      return null;
    }
  }

  /**
   * Build authentication headers from target config
   */
  private buildHeaders(targetConfig: any): Record<string, string> {
    const headers: Record<string, string> = {};

    // Add session cookie if present
    if (targetConfig.sessionCookie) {
      headers['Cookie'] = `${targetConfig.sessionCookie.name}=${targetConfig.sessionCookie.value}`;
    }

    // Add JWT token if present
    if (targetConfig.jwtToken) {
      headers['Authorization'] = `Bearer ${targetConfig.jwtToken}`;
    }

    // Add OAuth2 header if present
    if (targetConfig.oauth2Header) {
      headers['Authorization'] = `Bearer ${targetConfig.oauth2Header.token}`;
    }

    // Add custom headers if present
    if (targetConfig.customHeaders) {
      Object.assign(headers, targetConfig.customHeaders);
    }

    return headers;
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
