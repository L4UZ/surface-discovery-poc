/**
 * Passive reconnaissance stage
 * Subdomain enumeration and DNS resolution
 */

import { ToolRunner } from '../tools/runner.js';
import { SubfinderParser, DNSXParser } from '../tools/parsers.js';
import { logger, logStage } from '../utils/logger.js';
import type { DiscoveryConfig } from '../config.js';
import type { Subdomain, DomainInfo, DNSRecords, WHOISData } from '../models/index.js';

/**
 * Results from passive discovery stage
 */
export interface PassiveResults {
  subdomains: string[];
  totalSubdomains: number;
  dnsRecords: Map<string, DNSRecords>;
  uniqueIps: Set<string>;
  whoisData?: WHOISData;
}

/**
 * Passive reconnaissance stage
 */
export class PassiveDiscovery {
  private config: DiscoveryConfig;
  private runner: ToolRunner;

  /**
   * Create passive discovery stage
   * @param config - Discovery configuration
   */
  constructor(config: DiscoveryConfig) {
    this.config = config;
    this.runner = new ToolRunner(config.subfinderTimeout);
  }

  /**
   * Execute passive discovery stage
   * @param targetDomain - Root domain to discover
   * @returns Passive discovery results
   */
  async run(targetDomain: string): Promise<PassiveResults> {
    logStage('passive', 'start', { domain: targetDomain });

    const results: PassiveResults = {
      subdomains: [],
      totalSubdomains: 0,
      dnsRecords: new Map(),
      uniqueIps: new Set(),
    };

    try {
      // Phase 1: Subdomain enumeration
      const subdomains = await this.enumerateSubdomains(targetDomain);
      results.subdomains = subdomains;
      results.totalSubdomains = subdomains.length;
      logger.info(`Discovered ${results.totalSubdomains} subdomains`);

      // Phase 2: DNS resolution for root domain and all subdomains
      const dnsResults = await this.collectDnsRecords(targetDomain, subdomains);
      results.dnsRecords = dnsResults;

      // Extract unique IPs
      for (const dnsData of dnsResults.values()) {
        if (dnsData.a) {
          dnsData.a.forEach((ip) => results.uniqueIps.add(ip));
        }
        if (dnsData.aaaa) {
          dnsData.aaaa.forEach((ip) => results.uniqueIps.add(ip));
        }
      }

      logger.info(
        `Collected DNS records for ${dnsResults.size} hosts, ${results.uniqueIps.size} unique IPs`,
      );

      logStage('passive', 'complete', {
        subdomains: results.totalSubdomains,
        uniqueIps: results.uniqueIps.size,
      });

      return results;
    } catch (error) {
      logStage('passive', 'error', { error: String(error) });
      throw error;
    }
  }

  /**
   * Enumerate subdomains using subfinder
   * @param domain - Target domain
   * @returns List of discovered subdomains
   */
  private async enumerateSubdomains(domain: string): Promise<string[]> {
    logger.debug(`Enumerating subdomains for ${domain}`);
    const allSubdomains = new Set<string>();

    try {
      const output = await this.runner.runSubfinder(
        domain,
        this.config.subfinderTimeout,
        true,
      );

      const subdomains = SubfinderParser.parse(output);
      subdomains.forEach((subdomain) => allSubdomains.add(subdomain));
      logger.debug(`Subfinder found ${subdomains.length} subdomains`);
    } catch (error) {
      logger.error(`Subfinder execution failed: ${error}`);
    }

    // Apply limit if configured
    let limitedSubdomains = Array.from(allSubdomains);
    if (this.config.maxSubdomains && this.config.maxSubdomains > 0) {
      limitedSubdomains = limitedSubdomains.slice(0, this.config.maxSubdomains);
      logger.debug(`Limited to ${this.config.maxSubdomains} subdomains`);
    }

    return limitedSubdomains.sort();
  }

  /**
   * Collect DNS records for domain and subdomains
   * @param domain - Target root domain
   * @param subdomains - List of discovered subdomains to resolve
   * @returns Map of hostnames to DNS records
   */
  private async collectDnsRecords(
    domain: string,
    subdomains: string[],
  ): Promise<Map<string, DNSRecords>> {
    logger.debug(
      `Collecting DNS records for ${domain} and ${subdomains.length} subdomains`,
    );

    const dnsData = new Map<string, DNSRecords>();

    try {
      // Always get full records for root domain
      logger.debug(`Querying full DNS records for root domain: ${domain}`);
      const rootOutput = await this.runner.runDnsx(
        [domain],
        ['A', 'AAAA', 'MX', 'TXT', 'NS'],
        this.config.dnsxTimeout,
      );

      const rootDnsData = DNSXParser.parse(rootOutput);
      rootDnsData.forEach((value, key) => dnsData.set(key, value));

      // Resolve subdomains if present (A and AAAA records only for efficiency)
      if (subdomains.length > 0) {
        logger.info(`Resolving ${subdomains.length} subdomains to IP addresses...`);
        const subdomainOutput = await this.runner.runDnsx(
          subdomains,
          ['A', 'AAAA'],
          this.config.dnsxTimeout,
        );

        const subdomainDnsData = DNSXParser.parse(subdomainOutput);
        subdomainDnsData.forEach((value, key) => dnsData.set(key, value));

        logger.info(
          `DNS resolution complete: ${subdomainDnsData.size}/${subdomains.length} subdomains returned records`,
        );
      }

      logger.debug(`Collected DNS records for ${dnsData.size} hosts`);
    } catch (error) {
      logger.error(`DNS collection failed: ${error}`);
      throw error;
    }

    return dnsData;
  }

  /**
   * Convert PassiveResults to DomainInfo model
   * @param target - Root domain
   * @param results - Passive discovery results
   * @returns DomainInfo object
   */
  toDomainInfo(target: string, results: PassiveResults): DomainInfo {
    const subdomainObjects: Subdomain[] = [];
    let resolvedCount = 0;

    for (const subdomainName of results.subdomains) {
      // Get DNS records if available
      const dnsRecords = results.dnsRecords.get(subdomainName);

      // Extract IPs from DNS
      const ips: string[] = [];
      if (dnsRecords) {
        if (dnsRecords.a) {
          ips.push(...dnsRecords.a);
        }
        if (dnsRecords.aaaa) {
          ips.push(...dnsRecords.aaaa);
        }
        if (ips.length > 0) {
          resolvedCount++;
        }
      }

      const subdomain: Subdomain = {
        name: subdomainName,
        ips,
        status: 'unknown',
        dnsRecords,
        discoveredVia: 'passive',
        discoveredAt: new Date(),
      };

      subdomainObjects.push(subdomain);
    }

    // Log IP resolution statistics
    logger.info(
      `DNS resolution: ${resolvedCount}/${subdomainObjects.length} subdomains resolved to IPs`,
    );

    if (resolvedCount === 0) {
      logger.warn(
        'No subdomains resolved to IP addresses - port scanning and active discovery will be skipped',
      );
    }

    // Build DomainInfo
    const domainInfo: DomainInfo = {
      rootDomain: target,
      subdomains: subdomainObjects,
      dnsRecords: results.dnsRecords.get(target),
      whois: results.whoisData,
      totalSubdomains: subdomainObjects.length,
      liveSubdomains: 0, // Will be updated in active discovery
    };

    return domainInfo;
  }
}
