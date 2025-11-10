/**
 * Main discovery result models
 */

import { z } from 'zod';
import { domainInfoSchema } from './domain.js';
import { serviceSchema, technologySchema } from './service.js';

/**
 * Discovery pipeline stages
 */
export enum DiscoveryStage {
  INITIALIZED = 'initialized',
  PASSIVE_DISCOVERY = 'passive_discovery',
  PORT_DISCOVERY = 'port_discovery',
  ACTIVE_DISCOVERY = 'active_discovery',
  DEEP_DISCOVERY = 'deep_discovery',
  ENRICHMENT = 'enrichment',
  AUTHENTICATED_DISCOVERY = 'authenticated_discovery',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export const discoveryStageSchema = z.nativeEnum(DiscoveryStage);

/**
 * Timeline event during discovery
 */
export const timelineEventSchema = z.object({
  /** Event timestamp */
  timestamp: z.date().default(() => new Date()),
  /** Discovery stage */
  stage: discoveryStageSchema,
  /** Event description */
  event: z.string(),
  /** Event message (alias for event) */
  message: z.string().optional(),
  /** Additional details */
  details: z.record(z.any()).optional(),
});

export type TimelineEvent = z.infer<typeof timelineEventSchema>;

/**
 * Metadata about the discovery execution
 */
export const discoveryMetadataSchema = z.object({
  /** Target URL/domain */
  target: z.string(),
  /** Unique scan identifier */
  scanId: z.string(),
  /** Scan start time */
  startTime: z.date().default(() => new Date()),
  /** Scan end time */
  endTime: z.date().optional(),
  /** Duration in seconds */
  durationSeconds: z.number().nonnegative().optional(),
  /** Discovery depth level */
  discoveryDepth: z.enum(['shallow', 'normal', 'deep']).default('normal'),
  /** Versions of tools used */
  toolVersions: z.record(z.string()).default({}),
  /** Current discovery status */
  status: discoveryStageSchema.default(DiscoveryStage.INITIALIZED),
  /** Error message if failed */
  error: z.string().optional(),
});

export type DiscoveryMetadata = z.infer<typeof discoveryMetadataSchema>;

/**
 * Discovered API endpoint or URL path
 */
export const endpointSchema = z.object({
  /** Full endpoint URL */
  url: z.string().url(),
  /** HTTP method */
  method: z.string().default('GET'),
  /** Response status code */
  statusCode: z.number().int().min(100).max(599).optional(),
  /** Discovery source: crawl|js_analysis|sitemap|etc */
  discoveredVia: z.string(),
  /** URL parameters */
  parameters: z.array(z.string()).default([]),
  /** Requires authentication */
  requiresAuth: z.boolean().optional(),
});

export type Endpoint = z.infer<typeof endpointSchema>;

/**
 * Pentest focus recommendation
 */
export const recommendationSchema = z.object({
  /** Recommendation category */
  category: z.string(),
  /** Priority: high|medium|low */
  priority: z.enum(['high', 'medium', 'low']),
  /** Specific areas to focus on */
  areas: z.array(z.string()),
  /** Why this is recommended */
  rationale: z.string().optional(),
});

export type Recommendation = z.infer<typeof recommendationSchema>;

/**
 * Discovery statistics summary
 */
export const statisticsSchema = z.object({
  /** Total subdomains discovered */
  totalSubdomains: z.number().int().nonnegative().default(0),
  /** Live/responsive services */
  liveServices: z.number().int().nonnegative().default(0),
  /** Unique technologies detected */
  technologiesDetected: z.number().int().nonnegative().default(0),
  /** Total endpoints discovered */
  endpointsDiscovered: z.number().int().nonnegative().default(0),
  /** Total endpoints (alias for compatibility) */
  totalEndpoints: z.number().int().nonnegative().default(0),
  /** Total forms discovered */
  totalForms: z.number().int().nonnegative().default(0),
  /** Authenticated endpoints count */
  authenticatedEndpoints: z.number().int().nonnegative().default(0),
  /** Total ports scanned across all hosts */
  totalPortsScanned: z.number().int().nonnegative().default(0),
  /** Total open ports discovered */
  openPortsFound: z.number().int().nonnegative().default(0),
  /** Total open ports (alias for compatibility) */
  totalOpenPorts: z.number().int().nonnegative().default(0),
  /** Number of hosts with open ports */
  hostsWithOpenPorts: z.number().int().nonnegative().default(0),
  /** Estimated discovery completeness (0.0 - 1.0) */
  coverageCompleteness: z.number().min(0.0).max(1.0).default(0.0),
});

export type Statistics = z.infer<typeof statisticsSchema>;

/**
 * Complete discovery result output
 */
export const discoveryResultSchema = z.object({
  /** Scan metadata */
  metadata: discoveryMetadataSchema,
  /** Timeline of discovery events */
  discoveryTimeline: z.array(timelineEventSchema).default([]),
  /** Timeline (alias for discoveryTimeline) */
  timeline: z.array(timelineEventSchema).optional(),
  /** Domain intelligence */
  domains: domainInfoSchema.optional(),
  /** Live web services */
  services: z.array(serviceSchema).default([]),
  /** All detected technologies */
  technologies: z.array(technologySchema).default([]),
  /** Discovered endpoints */
  endpoints: z.array(endpointSchema).default([]),
  /** Pentest focus recommendations */
  recommendations: z.array(recommendationSchema).default([]),
  /** Infrastructure intelligence (cloud providers, CDN, ASN) */
  infrastructure: z.record(z.any()).default({}),
  /** Summary statistics */
  statistics: statisticsSchema.default({}),
});

export type DiscoveryResult = z.infer<typeof discoveryResultSchema>;

/**
 * Helper functions for discovery results
 */
export class DiscoveryResultHelper {
  /**
   * Add event to timeline
   */
  static addTimelineEvent(
    result: DiscoveryResult,
    stage: DiscoveryStage,
    event: string,
    details?: Record<string, unknown>
  ): DiscoveryResult {
    return {
      ...result,
      discoveryTimeline: [
        ...result.discoveryTimeline,
        {
          timestamp: new Date(),
          stage,
          event,
          details,
        },
      ],
    };
  }

  /**
   * Recalculate statistics from current data
   */
  static updateStatistics(result: DiscoveryResult): DiscoveryResult {
    const statistics: Statistics = { ...result.statistics };

    if (result.domains) {
      statistics.totalSubdomains = result.domains.subdomains.length;

      // Calculate port statistics
      let totalPortsScanned = 0;
      let totalOpenPorts = 0;
      let hostsWithOpenPorts = 0;

      for (const subdomain of result.domains.subdomains) {
        totalPortsScanned += subdomain.totalPortsScanned;
        totalOpenPorts += subdomain.openPortsCount;
        if (subdomain.openPortsCount > 0) {
          hostsWithOpenPorts++;
        }
      }

      statistics.totalPortsScanned = totalPortsScanned;
      statistics.openPortsFound = totalOpenPorts;
      statistics.hostsWithOpenPorts = hostsWithOpenPorts;
    }

    statistics.liveServices = result.services.length;
    statistics.technologiesDetected = result.technologies.length;
    statistics.endpointsDiscovered = result.endpoints.length;

    // Estimate completeness (simple heuristic)
    let completenessScore = 0.0;
    if (result.domains && result.domains.totalSubdomains > 0) {
      completenessScore += 0.3;
    }
    if (statistics.liveServices > 0) {
      completenessScore += 0.3;
    }
    if (statistics.endpointsDiscovered > 10) {
      completenessScore += 0.2;
    }
    if (statistics.technologiesDetected > 0) {
      completenessScore += 0.2;
    }

    statistics.coverageCompleteness = Math.min(completenessScore, 1.0);

    return {
      ...result,
      statistics,
    };
  }
}
