/**
 * Port discovery stage - network-level port scanning
 * Uses naabu for fast port scanning across discovered hosts
 */

import { ToolRunner } from '../tools/runner.js';
import { NaabuParser } from '../tools/parsers.js';
import { logger, logStage } from '../utils/logger.js';
import type { DiscoveryConfig } from '../config.js';
import type { Subdomain } from '../models/index.js';

/**
 * Results from port discovery stage
 */
export interface PortDiscoveryResults {
  totalHostsScanned: number;
  totalPortsScanned: number;
  totalOpenPorts: number;
  portsByHost: Record<string, number>;
}

/**
 * Port configuration for scanning
 */
interface PortConfig {
  ports?: string;
  topPorts?: number;
  rate: number;
}

/**
 * Port scanning stage using naabu
 */
export class PortDiscovery {
  private config: DiscoveryConfig;
  private runner: ToolRunner;

  constructor(config: DiscoveryConfig) {
    this.config = config;
    this.runner = new ToolRunner(config.naabuTimeout);
    logger.debug(`Port discovery initialized with timeout: ${config.naabuTimeout}s`);
  }

  /**
   * Execute port discovery stage
   * @param subdomains - List of discovered subdomains to scan
   * @returns Port discovery results
   */
  async run(subdomains: Subdomain[]): Promise<PortDiscoveryResults> {
    logStage('port_discovery', 'start', { totalSubdomains: subdomains.length });

    const results: PortDiscoveryResults = {
      totalHostsScanned: 0,
      totalPortsScanned: 0,
      totalOpenPorts: 0,
      portsByHost: {},
    };

    // Filter subdomains that have IP addresses
    const scannableSubdomains = subdomains.filter((sub) => sub.ips && sub.ips.length > 0);
    const filteredOut = subdomains.length - scannableSubdomains.length;

    logger.info(`Filtered: ${filteredOut}, Scannable: ${scannableSubdomains.length}`);

    if (filteredOut > 0) {
      logger.warn(
        `Filtered out ${filteredOut}/${subdomains.length} subdomains with no resolved IPs`
      );
    }

    if (scannableSubdomains.length === 0) {
      logger.warn('No subdomains with resolved IPs to scan - skipping port discovery');
      return results;
    }

    logger.info(`Scanning ${scannableSubdomains.length} subdomains with resolved IPs`);

    // Prepare hosts for scanning (use IPs for better reliability)
    const hostsToScan: string[] = [];
    const subdomainByIp = new Map<string, Subdomain>();

    for (const subdomain of scannableSubdomains) {
      for (const ip of subdomain.ips) {
        hostsToScan.push(ip);
        subdomainByIp.set(ip, subdomain);
      }
    }

    logger.info(
      `Built hosts list: ${hostsToScan.length} IPs from ${scannableSubdomains.length} subdomains`
    );

    // Determine port configuration based on depth and host count
    const portConfig = this.getPortConfig(hostsToScan.length);
    logger.info(
      `Port config: ports=${portConfig.ports ?? 'none'}, topPorts=${portConfig.topPorts ?? 'none'}, rate=${portConfig.rate}`
    );

    // Log progress estimate for deep scans
    if (this.config.depth === 'deep') {
      const estimatedTime = this.estimateScanTime(
        hostsToScan.length,
        portConfig.ports,
        portConfig.topPorts,
        portConfig.rate
      );
      logger.info(
        `Deep port scan starting: ${hostsToScan.length} hosts, estimated time: ${estimatedTime.toFixed(1)} minutes`
      );
    }

    try {
      // Run naabu port scan
      logger.info(
        `Calling naabu with ${hostsToScan.length} hosts, timeout=${this.config.naabuTimeout}s`
      );
      const output = await this.runner.runNaabu(
        hostsToScan,
        portConfig.ports,
        portConfig.topPorts,
        portConfig.rate,
        this.config.naabuTimeout
      );

      logger.info('naabu completed, parsing output...');

      // Parse results
      results.totalHostsScanned = hostsToScan.length;
      const portData = NaabuParser.parse(output);

      // Update subdomain objects with port scan results
      for (const [ip, ports] of portData.entries()) {
        const subdomain = subdomainByIp.get(ip);
        if (subdomain) {
          subdomain.openPorts = ports;
          subdomain.openPortsCount = ports.length;
          results.totalOpenPorts += ports.length;
          results.portsByHost[subdomain.name] = ports.length;
        }
      }

      // Calculate total ports scanned
      if (portConfig.topPorts) {
        results.totalPortsScanned = hostsToScan.length * portConfig.topPorts;
      } else if (portConfig.ports === '-') {
        results.totalPortsScanned = hostsToScan.length * 65535;
      } else {
        results.totalPortsScanned = hostsToScan.length * 100; // Conservative estimate
      }

      logger.info(
        `Port discovery complete: ${results.totalOpenPorts} open ports found across ${Object.keys(results.portsByHost).length} hosts`
      );

      logStage('port_discovery', 'complete', {
        openPorts: results.totalOpenPorts,
        hostsWithPorts: Object.keys(results.portsByHost).length,
      });

      return results;
    } catch (error) {
      logStage('port_discovery', 'error', { error: String(error) });
      throw error;
    }
  }

  /**
   * Get port configuration based on discovery depth and host count
   * Adaptive configuration: For deep scans with many hosts, use top 10K ports
   * instead of full range to stay within timeout limits
   */
  private getPortConfig(hostCount: number): PortConfig {
    const depth = this.config.depth;

    if (depth === 'shallow') {
      // Top 100 ports, conservative rate
      return { topPorts: 100, rate: 1000 };
    } else if (depth === 'normal') {
      // Top 1000 ports, moderate rate
      return { topPorts: 1000, rate: 1500 };
    } else if (depth === 'deep') {
      // Adaptive configuration based on host count
      if (hostCount > 50) {
        logger.info(
          `Deep scan with ${hostCount} hosts: using top 10K ports instead of full range to stay within timeout`
        );
        return { topPorts: 10000, rate: 3000 };
      } else {
        logger.info(`Deep scan with ${hostCount} hosts: using full port range (65535)`);
        return { ports: '-', rate: 3000 };
      }
    } else {
      // Fallback to normal
      return { topPorts: 1000, rate: 1500 };
    }
  }

  /**
   * Estimate port scan time in minutes
   */
  private estimateScanTime(
    hostCount: number,
    ports?: string,
    topPorts?: number,
    rate: number = 1000
  ): number {
    // Calculate total port checks
    let totalChecks: number;
    if (topPorts) {
      totalChecks = hostCount * topPorts;
    } else if (ports === '-') {
      totalChecks = hostCount * 65535;
    } else {
      totalChecks = hostCount * 1000; // Conservative estimate
    }

    // Estimate time: total_checks / rate / 60 (convert to minutes)
    // Add 20% overhead for network latency and processing
    const estimatedSeconds = (totalChecks / rate) * 1.2;
    return estimatedSeconds / 60;
  }
}
