/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/**
 * Parsers for external tool outputs
 * Converts raw tool output (JSONL, text) to typed data structures
 */

import { logger } from '../utils/logger.js';
import type {
  Service,
  Technology,
  DNSRecords,
  SecurityHeaders,
  PortScanResult,
} from '../models/index.js';
import z from 'zod';

/**
 * Parse subfinder output to list of subdomains
 */
export class SubfinderParser {
  /**
   * Parse subfinder output to list of subdomains
   * @param output - Raw subfinder stdout (one subdomain per line)
   * @returns List of discovered subdomains
   */
  static parse(output: string): string[] {
    const subdomains: string[] = [];

    for (const line of output.trim().split('\n')) {
      const trimmedLine = line.trim();
      if (trimmedLine && !trimmedLine.startsWith('#')) {
        subdomains.push(trimmedLine);
      }
    }

    logger.debug(`Parsed ${subdomains.length} subdomains from subfinder`);
    return subdomains;
  }
}

/**
 * Parse httpx JSON output
 */
export class HTTPXParser {
  /**
   * Parse httpx JSON output to Service objects
   * @param output - Raw httpx JSON output (one JSON object per line)
   * @returns List of Service objects
   */
  static parse(output: string): Service[] {
    const services: Service[] = [];

    for (const line of output.trim().split('\n')) {
      if (!line.trim()) {
        continue;
      }

      try {
        const data = JSON.parse(line);
        const service = this.parseService(data);
        if (service) {
          services.push(service);
        }
      } catch (error) {
        if (error instanceof SyntaxError) {
          logger.warn(`Failed to parse httpx JSON line: ${error.message}`);
        } else {
          logger.error(`Error parsing httpx output: ${String(error)}`);
        }
      }
    }

    logger.debug(`Parsed ${services.length} services from httpx`);
    return services;
  }

  /**
   * Convert httpx JSON object to Service model
   * @param data - Parsed JSON object from httpx
   * @returns Service object or null if parsing fails
   */
  private static parseService(data: any): Service | null {
    try {
      // Extract technologies
      const technologies: Technology[] = [];
      if (data.tech && Array.isArray(data.tech)) {
        for (const techName of data.tech) {
          technologies.push({
            name: techName,
            category: 'web',
            confidence: 0.8,
            detectedFrom: ['httpx'],
          });
        }
      }

      // Extract security headers
      let securityHeaders: SecurityHeaders | undefined;
      if (data.header) {
        const headers = data.header;
        securityHeaders = {
          contentSecurityPolicy: headers['content-security-policy'] ?? undefined,
          strictTransportSecurity: headers['strict-transport-security'] ?? undefined,
          xFrameOptions: headers['x-frame-options'] ?? undefined,
          xContentTypeOptions: headers['x-content-type-options'] ?? undefined,
          xXssProtection: headers['x-xss-protection'] ?? undefined,
          referrerPolicy: headers['referrer-policy'] ?? undefined,
          permissionsPolicy: headers['permissions-policy'] ?? undefined,
        };
      }

      // Build Service object
      const service: Service = {
        url: data.url ?? '',
        statusCode: data.status_code ?? 0,
        contentLength: data.content_length ?? undefined,
        title: data.title ?? undefined,
        server: data.webserver ?? undefined,
        technologies,
        securityHeaders,
        responseTime: data.time ?? undefined,
        redirectsTo: data.final_url ?? undefined,
      };

      return service;
    } catch (error) {
      logger.error(`Error creating Service from httpx data: ${String(error)}`);
      return null;
    }
  }
}

/**
 * Parse dnsx JSON output
 */
export class DNSXParser {
  /**
   * Parse dnsx JSON output to DNS records
   * @param output - Raw dnsx JSON output (one JSON object per line)
   * @returns Map of hostnames to DNSRecords
   */
  static parse(output: string): Map<string, DNSRecords> {
    const dnsData = new Map<string, DNSRecords>();

    for (const line of output.trim().split('\n')) {
      if (!line.trim()) {
        continue;
      }

      try {
        const rawData = JSON.parse(line);

        // TODO: Move schema to models
        const data = z
          .object({
            host: z.string(),
            a: z.array(z.string()).optional().default([]),
            aaaa: z.array(z.string()).optional().default([]),
            mx: z.array(z.string()).optional().default([]),
            txt: z.array(z.string()).optional().default([]),
            ns: z.array(z.string()).optional().default([]),
            cname: z.array(z.string()).optional().default([]),
          })
          .parse(rawData);

        const hostname = data.host;

        if (!hostname) {
          continue;
        }

        // Initialize or get existing records
        if (!dnsData.has(hostname)) {
          dnsData.set(hostname, {
            a: [],
            aaaa: [],
            mx: [],
            txt: [],
            ns: [],
            cname: undefined,
          });
        }

        const records = dnsData.get(hostname);

        // Parse different record types
        records.a.push(...data.a);

        records.aaaa.push(...data.aaaa);

        records.mx.push(...data.mx);

        records.txt.push(...data.txt);

        records.ns.push(...data.ns);

        if (data.cname.length > 0) {
          records.cname = data.cname[0];
        }
      } catch (error) {
        if (error instanceof SyntaxError) {
          logger.warn(`Failed to parse dnsx JSON line: ${error.message}`);
        } else {
          logger.error(`Error parsing dnsx output: ${String(error)}`);
        }
      }
    }

    logger.debug(`Parsed DNS records for ${dnsData.size} hosts`);
    return dnsData;
  }
}

/**
 * Parse naabu JSON output
 */
export class NaabuParser {
  /**
   * Parse naabu JSON output to port scan results
   * @param output - Raw naabu JSON output (one JSON object per line)
   * @returns Map of hosts to PortScanResult arrays
   */
  static parse(output: string): Map<string, PortScanResult[]> {
    const portData = new Map<string, PortScanResult[]>();

    for (const line of output.trim().split('\n')) {
      if (!line.trim()) {
        continue;
      }

      try {
        const rawData = JSON.parse(line);

        // TODO: Improve this schema
        const data = z
          .object({
            host: z.string().optional(),
            ip: z.string().optional(),
            port: z.number().optional(),
            service: z.string().optional(),
          })
          .parse(rawData);

        const host = data.host ?? data.ip ?? '';
        const port = data.port;

        if (!host || !port) {
          continue;
        }

        // Initialize or get existing port list
        if (!portData.has(host)) {
          portData.set(host, []);
        }

        const portResult: PortScanResult = {
          port,
          state: 'open',
          service: data.service ?? undefined,
        };

        portData.get(host).push(portResult);
      } catch (error) {
        if (error instanceof SyntaxError) {
          logger.warn(`Failed to parse naabu JSON line: ${error.message}`);
        } else {
          logger.error(`Error parsing naabu output: ${String(error)}`);
        }
      }
    }

    logger.debug(`Parsed port data for ${portData.size} hosts`);
    return portData;
  }
}

/**
 * Parse katana JSON output
 */
export class KatanaParser {
  /**
   * Parse katana JSON output to discovered URLs
   * @param output - Raw katana JSON output (one JSON object per line)
   * @returns List of discovered URLs with metadata
   */
  static parse(output: string): Array<{
    url: string;
    method?: string;
    source?: string;
    tag?: string;
    attribute?: string;
  }> {
    const urls: Array<{
      url: string;
      method?: string;
      source?: string;
      tag?: string;
      attribute?: string;
    }> = [];

    for (const line of output.trim().split('\n')) {
      if (!line.trim()) {
        continue;
      }

      try {
        const rawData = JSON.parse(line);

        const data = z
          .object({
            endpoint: z.string().optional(),
            url: z.string().optional(),
            method: z.string().optional(),
            source: z.string().optional(),
            tag: z.string().optional(),
            attribute: z.string().optional(),
          })
          .parse(rawData);

        const url = data.endpoint || data.url;

        if (!url) {
          continue;
        }

        urls.push({
          url,
          method: data.method,
          source: data.source,
          tag: data.tag,
          attribute: data.attribute,
        });
      } catch (error) {
        if (error instanceof SyntaxError) {
          logger.warn(`Failed to parse katana JSON line: ${error.message}`);
        } else {
          logger.error(`Error parsing katana output: ${String(error)}`);
        }
      }
    }

    logger.debug(`Parsed ${urls.length} URLs from katana`);
    return urls;
  }
}

/**
 * Generic parser for line-separated subdomain lists
 * @param rawOutput - Raw tool output with one subdomain per line
 * @returns List of unique subdomains
 */
export function parseSubdomainList(rawOutput: string): string[] {
  const subdomains = new Set<string>();

  for (let line of rawOutput.trim().split('\n')) {
    line = line.trim();

    if (line && !line.startsWith('#') && !line.startsWith('//') && !line.startsWith(';')) {
      // Remove protocol if present
      if (line.includes('://')) {
        line = line.split('://', 2)[1];
      }

      // Remove path if present
      if (line.includes('/')) {
        line = line.split('/', 2)[0];
      }

      // Remove port if present (but not for IPv6)
      if (line.includes(':') && (line.match(/:/g) || []).length === 1) {
        line = line.split(':', 2)[0];
      }

      subdomains.add(line.toLowerCase());
    }
  }

  return Array.from(subdomains).sort();
}
