/**
 * Enrichment stage - infrastructure intelligence gathering
 * Collects cloud provider, CDN, and ASN information
 */

import { ToolRunner } from '../tools/runner.js';
import { logger, logStage } from '../utils/logger.js';
import { getCloudProvider, getCdnProvider } from '../utils/helpers.js';
import type { DiscoveryConfig } from '../config.js';
import type { Subdomain } from '../models/index.js';

/**
 * Infrastructure information for a subdomain
 */
export interface InfrastructureInfo {
  cloudProvider?: string;
  cdnProvider?: string;
  asn?: string;
  asnOrg?: string;
}

/**
 * Results from enrichment stage
 */
export interface EnrichmentResults {
  totalEnriched: number;
  cloudProviders: Record<string, number>;
  cdnProviders: Record<string, number>;
  asnCounts: Record<string, number>;
}

/**
 * Enrichment stage - infrastructure intelligence
 */
export class Enrichment {
  private config: DiscoveryConfig;
  private runner: ToolRunner;

  /**
   * Create enrichment stage
   * @param config - Discovery configuration
   */
  constructor(config: DiscoveryConfig) {
    this.config = config;
    this.runner = new ToolRunner(config.dnsxTimeout);
  }

  /**
   * Execute enrichment stage
   * @param subdomains - List of subdomains to enrich
   * @returns Enrichment results
   */
  run(subdomains: Subdomain[]): EnrichmentResults {
    logStage('enrichment', 'start', { totalSubdomains: subdomains.length });

    const results: EnrichmentResults = {
      totalEnriched: 0,
      cloudProviders: {},
      cdnProviders: {},
      asnCounts: {},
    };

    if (subdomains.length === 0) {
      logger.warn('No subdomains to enrich');
      return results;
    }

    try {
      // Enrich each subdomain with infrastructure info
      for (const subdomain of subdomains) {
        const infraInfo = this.enrichSubdomain(subdomain);

        if (infraInfo) {
          // Update subdomain object
          subdomain.cloudProvider = infraInfo.cloudProvider;
          subdomain.cdnProvider = infraInfo.cdnProvider;

          // Update statistics
          results.totalEnriched++;

          if (infraInfo.cloudProvider) {
            results.cloudProviders[infraInfo.cloudProvider] =
              (results.cloudProviders[infraInfo.cloudProvider] || 0) + 1;
          }

          if (infraInfo.cdnProvider) {
            results.cdnProviders[infraInfo.cdnProvider] =
              (results.cdnProviders[infraInfo.cdnProvider] || 0) + 1;
          }

          if (infraInfo.asn) {
            results.asnCounts[infraInfo.asn] = (results.asnCounts[infraInfo.asn] || 0) + 1;
          }
        }
      }

      logger.info(
        `Enrichment complete: ${results.totalEnriched}/${subdomains.length} subdomains enriched`
      );

      logStage('enrichment', 'complete', {
        enriched: results.totalEnriched,
        cloudProviders: Object.keys(results.cloudProviders).length,
        cdnProviders: Object.keys(results.cdnProviders).length,
      });

      return results;
    } catch (error) {
      logStage('enrichment', 'error', { error: String(error) });
      throw error;
    }
  }

  /**
   * Enrich a single subdomain with infrastructure information
   */
  private enrichSubdomain(subdomain: Subdomain): InfrastructureInfo {
    try {
      // Extract infrastructure info from IPs
      const infraInfo: InfrastructureInfo = {
        cloudProvider: undefined,
        cdnProvider: undefined,
        asn: undefined,
        asnOrg: undefined,
      };

      if (subdomain.ips && subdomain.ips.length > 0) {
        // Check cloud provider based on IP
        const cloudProvider = getCloudProvider(subdomain.ips[0]);
        if (cloudProvider) {
          infraInfo.cloudProvider = cloudProvider;
        }

        // Check CDN provider based on CNAME
        if (subdomain.dnsRecords?.cname) {
          const cdnProvider = getCdnProvider(subdomain.dnsRecords.cname);
          if (cdnProvider) {
            infraInfo.cdnProvider = cdnProvider;
          }
        }
      }

      return infraInfo;
    } catch (error) {
      logger.debug(`Failed to enrich ${subdomain.name}: ${String(error)}`);
      return {
        cloudProvider: undefined,
        cdnProvider: undefined,
        asn: undefined,
        asnOrg: undefined,
      };
    }
  }
}
