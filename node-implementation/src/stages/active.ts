/**
 * Active discovery stage - HTTP probing and service detection
 * Uses httpx for HTTP/HTTPS probing with technology detection
 */

import { ToolRunner } from '../tools/runner.js';
import { HTTPXParser } from '../tools/parsers.js';
import { logger, logStage } from '../utils/logger.js';
import type { DiscoveryConfig } from '../config.js';
import type { Service, Subdomain } from '../models/index.js';

/**
 * Results from active discovery stage
 */
export interface ActiveResults {
  services: Service[];
  liveCount: number;
  deadCount: number;
  totalProbed: number;
}

/**
 * Active reconnaissance stage - HTTP probing and service detection
 */
export class ActiveDiscovery {
  private config: DiscoveryConfig;
  private runner: ToolRunner;

  /**
   * Create active discovery stage
   * @param config - Discovery configuration
   */
  constructor(config: DiscoveryConfig) {
    this.config = config;
    this.runner = new ToolRunner(config.httpxTimeout);
  }

  /**
   * Execute active discovery stage
   * @param subdomains - List of subdomains to probe
   * @returns Active discovery results
   */
  async run(subdomains: string[]): Promise<ActiveResults> {
    logStage('active', 'start', { totalSubdomains: subdomains.length });

    const results: ActiveResults = {
      services: [],
      liveCount: 0,
      deadCount: 0,
      totalProbed: subdomains.length,
    };

    try {
      // HTTP/HTTPS probing with httpx
      const services = await this.probeHttpServices(subdomains);
      results.services = services;
      results.liveCount = services.length;
      results.deadCount = results.totalProbed - results.liveCount;

      logger.info(
        `Active discovery complete: ${results.liveCount} live, ${results.deadCount} dead`
      );

      logStage('active', 'complete', {
        liveServices: results.liveCount,
        deadServices: results.deadCount,
      });

      return results;
    } catch (error) {
      logStage('active', 'error', { error: String(error) });
      throw error;
    }
  }

  /**
   * Probe subdomains for HTTP/HTTPS services
   */
  private async probeHttpServices(subdomains: string[]): Promise<Service[]> {
    logger.debug(`Probing ${subdomains.length} subdomains with httpx`);

    try {
      // Run httpx with tech detection and JSON output
      const output = await this.runner.runHttpx(
        subdomains,
        this.config.httpxTimeout,
        true, // tech detection
        true, // follow redirects
        true  // JSON output
      );

      // Parse JSON output
      const services = HTTPXParser.parse(output);
      logger.debug(`Discovered ${services.length} live services`);

      return services;
    } catch (error) {
      logger.error(`httpx execution failed: ${error}`);
      throw error;
    }
  }

  /**
   * Update subdomain objects with active discovery results
   * @param subdomains - List of subdomains to update
   * @param services - Discovered services
   */
  updateSubdomains(subdomains: Subdomain[], services: Service[]): void {
    // Create map of subdomain names to services
    const servicesByDomain = new Map<string, Service[]>();

    for (const service of services) {
      try {
        const url = new URL(service.url);
        const hostname = url.hostname;

        if (!servicesByDomain.has(hostname)) {
          servicesByDomain.set(hostname, []);
        }
        servicesByDomain.get(hostname)!.push(service);
      } catch (error) {
        logger.warn(`Failed to parse URL: ${service.url}`);
      }
    }

    // Update subdomain status based on discovered services
    for (const subdomain of subdomains) {
      const services = servicesByDomain.get(subdomain.name);
      if (services && services.length > 0) {
        subdomain.status = 'live';
        subdomain.services = services;
      } else {
        subdomain.status = 'dead';
      }
    }

    const liveCount = subdomains.filter((sub) => sub.status === 'live').length;
    logger.info(
      `Updated subdomain statuses: ${liveCount}/${subdomains.length} live`
    );
  }
}
