/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Core orchestration engine for discovery pipeline
 * Coordinates all discovery stages and manages result aggregation
 */

import { randomUUID } from 'crypto';
import { logger, logError } from './utils/logger.js';
import { extractDomain } from './utils/helpers.js';
import { getConfig, type DiscoveryConfig } from './config.js';
import {
  DiscoveryStage,
  type DiscoveryResult,
  type TimelineEvent,
  type DiscoveryMetadata,
  Service,
} from './models/index.js';
import { PassiveDiscovery } from './stages/passive.js';
import { PortDiscovery } from './stages/portDiscovery.js';
import { ActiveDiscovery } from './stages/active.js';
import { DeepDiscovery } from './stages/deep.js';
import { Enrichment } from './stages/enrichment.js';
import { AuthenticatedDiscovery } from './stages/authenticated.js';
import type { AuthenticationConfig } from './models/auth.js';

/**
 * Main orchestration engine for attack surface discovery
 */
export class DiscoveryEngine {
  private config: DiscoveryConfig;
  private result: DiscoveryResult | null = null;

  /**
   * Create discovery engine
   * @param config - Discovery configuration (uses default if not provided)
   */
  constructor(config?: DiscoveryConfig) {
    this.config = config ?? getConfig();
  }

  /**
   * Execute full discovery pipeline
   * @param targetUrl - Target URL or domain
   * @param authConfig - Optional authentication configuration
   * @returns Discovery result with all discovered data
   * @throws Error if target URL is invalid or discovery fails
   */
  async discover(targetUrl: string, authConfig?: AuthenticationConfig): Promise<DiscoveryResult> {
    // Extract and validate domain
    let targetDomain: string;
    try {
      targetDomain = extractDomain(targetUrl);
    } catch (error: any) {
      throw new Error(`Invalid target URL: ${error}`);
    }

    logger.info(`Starting discovery for ${targetDomain} (depth: ${this.config.depth})`);

    // Initialize result
    const scanId = randomUUID();
    const metadata: DiscoveryMetadata = {
      target: targetDomain,
      scanId,
      startTime: new Date(),
      discoveryDepth: this.config.depth,
      status: DiscoveryStage.INITIALIZED,
      toolVersions: {},
    };

    this.result = {
      metadata,
      domains: {
        rootDomain: targetDomain,
        subdomains: [],
        totalSubdomains: 0,
        liveSubdomains: 0,
      },
      services: [],
      endpoints: [],
      infrastructure: {
        cloudProviders: {},
        cdnProviders: {},
        asnMappings: {},
      },
      technologies: [],
      statistics: {
        totalSubdomains: 0,
        liveServices: 0,
        totalEndpoints: 0,
        totalForms: 0,
        totalOpenPorts: 0,
        hostsWithOpenPorts: 0,
        coverageCompleteness: 0,
        endpointsDiscovered: 0,
        technologiesDetected: 0,
        totalPortsScanned: 0,
        openPortsFound: 0,
      },
      discoveryTimeline: [],
      recommendations: [],
    };

    this.addTimelineEvent(DiscoveryStage.INITIALIZED, 'Discovery initialized', {
      target: targetDomain,
      depth: this.config.depth,
    });

    try {
      // Stage 1: Passive Discovery
      await this.runPassiveDiscovery(targetDomain);

      // Stage 1.5: Port Discovery
      await this.runPortDiscovery();

      // Stage 2: Active Discovery
      await this.runActiveDiscovery();

      // Stage 3: Deep Discovery
      await this.runDeepDiscovery();

      // Stage 4: Enrichment
      this.runEnrichment();

      // Stage 5: Authenticated Discovery (if configured)
      if (authConfig) {
        await this.runAuthenticatedDiscovery(authConfig);
      }

      // Finalize
      this.finalize();
    } catch (error: any) {
      logger.error(`Discovery failed: ${error}`);
      if (this.result) {
        this.result.metadata.status = DiscoveryStage.FAILED;
        this.result.metadata.error = String(error);
      }
      throw error;
    }

    return this.result;
  }

  /**
   * Execute passive discovery stage
   */
  private async runPassiveDiscovery(targetDomain: string): Promise<void> {
    logger.info('Stage 1: Passive Discovery');
    if (!this.result) return;

    this.result.metadata.status = DiscoveryStage.PASSIVE_DISCOVERY;
    this.addTimelineEvent(DiscoveryStage.PASSIVE_DISCOVERY, 'Starting passive reconnaissance');

    try {
      const passive = new PassiveDiscovery(this.config);
      const passiveResults = await passive.run(targetDomain);

      // Convert to DomainInfo
      const domainInfo = passive.toDomainInfo(targetDomain, passiveResults);
      this.result.domains = domainInfo;

      this.addTimelineEvent(DiscoveryStage.PASSIVE_DISCOVERY, 'Passive discovery completed', {
        subdomainsFound: passiveResults.subdomains.length,
        uniqueIps: passiveResults.uniqueIps.size,
      });

      logger.info(`Passive discovery complete: ${passiveResults.subdomains.length} subdomains`);
    } catch (error: any) {
      logError('Passive discovery failed', error);
      this.addTimelineEvent(DiscoveryStage.PASSIVE_DISCOVERY, `Passive discovery failed: ${error}`);
      throw error;
    }
  }

  /**
   * Execute port discovery stage
   */
  private async runPortDiscovery(): Promise<void> {
    logger.info('Stage 1.5: Port Discovery');
    if (!this.result) return;

    this.addTimelineEvent(DiscoveryStage.PORT_DISCOVERY, 'Starting port scanning');

    try {
      if (!this.result.domains?.subdomains || this.result.domains.subdomains.length === 0) {
        logger.warn('No subdomains found, skipping port discovery');
        return;
      }

      const portDiscovery = new PortDiscovery(this.config);
      const portResults = await portDiscovery.run(this.result.domains.subdomains);

      this.addTimelineEvent(DiscoveryStage.PORT_DISCOVERY, 'Port discovery completed', {
        hostsScanned: portResults.totalHostsScanned,
        openPortsFound: portResults.totalOpenPorts,
      });

      this.result.statistics.totalOpenPorts = portResults.totalOpenPorts;

      logger.info(
        `Port discovery complete: ${portResults.totalOpenPorts} open ports ` +
          `found across ${Object.keys(portResults.portsByHost).length} hosts`
      );
    } catch (error: any) {
      logError('Port discovery failed', error);
      this.addTimelineEvent(DiscoveryStage.PORT_DISCOVERY, `Port discovery failed: ${error}`);
      // Don't throw - port discovery failure shouldn't stop the pipeline
    }
  }

  /**
   * Execute active discovery stage
   */
  private async runActiveDiscovery(): Promise<void> {
    logger.info('Stage 2: Active Discovery');
    if (!this.result) return;

    this.result.metadata.status = DiscoveryStage.ACTIVE_DISCOVERY;
    this.addTimelineEvent(DiscoveryStage.ACTIVE_DISCOVERY, 'Starting active probing');

    try {
      if (!this.result.domains?.subdomains || this.result.domains.subdomains.length === 0) {
        logger.warn('No subdomains found, skipping active discovery');
        return;
      }

      const active = new ActiveDiscovery(this.config);
      const subdomainNames = this.result.domains.subdomains.map((s) => s.name);
      const activeResults = await active.run(subdomainNames);

      // Update subdomain statuses
      active.updateSubdomains(this.result.domains.subdomains, activeResults.services);

      // Store services
      this.result.services = activeResults.services;
      this.result.statistics.liveServices = activeResults.liveCount;
      this.result.domains.liveSubdomains = this.result.domains.subdomains.filter(
        (s) => s.status === 'live'
      ).length;

      // Extract technologies
      this.result.technologies = this.extractTechnologies(activeResults.services);

      this.addTimelineEvent(DiscoveryStage.ACTIVE_DISCOVERY, 'Active discovery completed', {
        liveServices: activeResults.liveCount,
        deadServices: activeResults.deadCount,
      });

      logger.info(`Active discovery complete: ${activeResults.liveCount} live services`);
    } catch (error: any) {
      logError('Active discovery failed', error);
      this.addTimelineEvent(DiscoveryStage.ACTIVE_DISCOVERY, `Active discovery failed: ${error}`);
      throw error;
    }
  }

  /**
   * Execute deep discovery stage
   */
  private async runDeepDiscovery(): Promise<void> {
    logger.info('Stage 3: Deep Discovery');
    if (!this.result) return;

    this.result.metadata.status = DiscoveryStage.DEEP_DISCOVERY;
    this.addTimelineEvent(DiscoveryStage.DEEP_DISCOVERY, 'Starting web crawling');

    try {
      if (!this.result.services || this.result.services.length === 0) {
        logger.warn('No live services found, skipping deep discovery');
        return;
      }

      const deep = new DeepDiscovery(this.config);
      const deepResults = await deep.run(this.result.services);

      // Store endpoints - flatten URLDiscoveryResult[] to get individual URLs
      this.result.endpoints = deepResults.urls.flatMap((result: any) => result.urls || []);
      this.result.statistics.totalEndpoints = deepResults.totalEndpoints;
      this.result.statistics.totalForms = deepResults.totalForms;

      this.addTimelineEvent(DiscoveryStage.DEEP_DISCOVERY, 'Deep discovery completed', {
        totalUrls: deepResults.totalUrls,
        totalEndpoints: deepResults.totalEndpoints,
        totalForms: deepResults.totalForms,
      });

      logger.info(
        `Deep discovery complete: ${deepResults.totalUrls} URLs, ${deepResults.totalEndpoints} endpoints`
      );
    } catch (error: any) {
      logError('Deep discovery failed', error);
      this.addTimelineEvent(DiscoveryStage.DEEP_DISCOVERY, `Deep discovery failed: ${error}`);
      // Don't throw - continue to enrichment
    }
  }

  /**
   * Execute enrichment stage
   */
  private runEnrichment(): void {
    logger.info('Stage 4: Enrichment');
    if (!this.result) return;

    this.result.metadata.status = DiscoveryStage.ENRICHMENT;
    this.addTimelineEvent(DiscoveryStage.ENRICHMENT, 'Starting infrastructure intelligence');

    try {
      if (!this.result.domains?.subdomains || this.result.domains.subdomains.length === 0) {
        logger.warn('No subdomains found, skipping enrichment');
        return;
      }

      const enrichment = new Enrichment(this.config);
      const enrichmentResults = enrichment.run(this.result.domains.subdomains);

      // Store infrastructure data
      this.result.infrastructure = {
        cloudProviders: enrichmentResults.cloudProviders,
        cdnProviders: enrichmentResults.cdnProviders,
        asnMappings: enrichmentResults.asnCounts,
      };

      this.addTimelineEvent(DiscoveryStage.ENRICHMENT, 'Enrichment completed', {
        enriched: enrichmentResults.totalEnriched,
        cloudProviders: Object.keys(enrichmentResults.cloudProviders).length,
      });

      logger.info(`Enrichment complete: ${enrichmentResults.totalEnriched} subdomains enriched`);
    } catch (error: any) {
      logError('Enrichment failed', error);
      this.addTimelineEvent(DiscoveryStage.ENRICHMENT, `Enrichment failed: ${error}`);
      // Don't throw - continue to finalization
    }
  }

  /**
   * Execute authenticated discovery stage
   */
  private async runAuthenticatedDiscovery(authConfig: AuthenticationConfig): Promise<void> {
    logger.info('Stage 5: Authenticated Discovery');
    if (!this.result) return;

    this.result.metadata.status = DiscoveryStage.AUTHENTICATED_DISCOVERY;
    this.addTimelineEvent(
      DiscoveryStage.AUTHENTICATED_DISCOVERY,
      'Starting authenticated crawling'
    );

    try {
      const authenticated = new AuthenticatedDiscovery(this.config);
      const authResults = await authenticated.run(authConfig);

      // Add authenticated endpoints to existing endpoints - flatten if needed
      const authUrls = Array.isArray(authResults.urls)
        ? authResults.urls.flatMap((r: any) => r.urls || [r])
        : [];
      this.result.endpoints.push(...authUrls);
      this.result.statistics.authenticatedEndpoints = authResults.authenticatedEndpointsCount;

      this.addTimelineEvent(
        DiscoveryStage.AUTHENTICATED_DISCOVERY,
        'Authenticated discovery completed',
        {
          totalUrls: authResults.totalUrls,
          authenticatedEndpoints: authResults.authenticatedEndpointsCount,
        }
      );

      logger.info(`Authenticated discovery complete: ${authResults.totalUrls} authenticated URLs`);
    } catch (error: any) {
      logError('Authenticated discovery failed', error);
      this.addTimelineEvent(
        DiscoveryStage.AUTHENTICATED_DISCOVERY,
        `Authenticated discovery failed: ${error}`
      );
      // Don't throw - continue to finalization
    }
  }

  /**
   * Finalize discovery and compute final statistics
   */
  private finalize(): void {
    if (!this.result) return;

    const endTime = new Date();
    const duration = (endTime.getTime() - this.result.metadata.startTime.getTime()) / 1000;

    this.result.metadata.endTime = endTime;
    this.result.metadata.durationSeconds = duration;
    this.result.metadata.status = DiscoveryStage.COMPLETED;

    // Update final statistics
    this.result.statistics.totalSubdomains = this.result.domains?.totalSubdomains ?? 0;

    this.addTimelineEvent(DiscoveryStage.COMPLETED, 'Discovery completed successfully', {
      duration: `${duration.toFixed(2)}s`,
      totalSubdomains: this.result.statistics.totalSubdomains,
      liveServices: this.result.statistics.liveServices,
    });

    logger.info(`Discovery completed in ${duration.toFixed(2)}s`);
  }

  /**
   * Add timeline event to result
   */
  private addTimelineEvent(
    stage: DiscoveryStage,
    message: string,
    details?: Record<string, any>
  ): void {
    if (!this.result) return;

    const event: TimelineEvent = {
      stage,
      timestamp: new Date(),
      message,
      details,
    };

    this.result.discoveryTimeline.push(event);
  }

  /**
   * Extract unique technologies from services
   */
  // TODO: Add types
  private extractTechnologies(services: Service[]): object[] {
    const techMap = new Map<string, object>();

    for (const service of services) {
      if (service.technologies) {
        for (const tech of service.technologies) {
          if (!techMap.has(tech.name)) {
            techMap.set(tech.name, tech);
          }
        }
      }
    }

    return Array.from(techMap.values());
  }
}
