/**
 * Domain-related data models and schemas
 */

import { z } from 'zod';

/**
 * Port scan result for a single port
 */
export const portScanResultSchema = z.object({
  /** Port number (1-65535) */
  port: z.number().int().min(1).max(65535),
  /** Protocol (tcp/udp) */
  protocol: z.enum(['tcp', 'udp']).default('tcp'),
  /** Port state (open/closed/filtered) */
  state: z.enum(['open', 'closed', 'filtered']),
  /** Service name (http, ssh, etc.) */
  service: z.string().optional(),
  /** Service version if detected */
  version: z.string().optional(),
  /** Timestamp when port was discovered */
  discoveredAt: z.date().default(() => new Date()),
});

export type PortScanResult = z.infer<typeof portScanResultSchema>;

/**
 * DNS records for a domain
 */
export const dnsRecordsSchema = z.object({
  /** A records (IPv4) */
  a: z.array(z.string()).default([]),
  /** AAAA records (IPv6) */
  aaaa: z.array(z.string()).default([]),
  /** MX records */
  mx: z.array(z.string()).default([]),
  /** TXT records */
  txt: z.array(z.string()).default([]),
  /** NS records */
  ns: z.array(z.string()).default([]),
  /** CNAME record */
  cname: z.string().optional(),
});

export type DNSRecords = z.infer<typeof dnsRecordsSchema>;

/**
 * WHOIS registration data
 */
export const whoisDataSchema = z.object({
  /** Domain registrar */
  registrar: z.string().optional(),
  /** Domain creation date */
  creationDate: z.date().optional(),
  /** Domain expiration date */
  expirationDate: z.date().optional(),
  /** Name servers */
  nameServers: z.array(z.string()).default([]),
  /** Domain status codes */
  status: z.array(z.string()).default([]),
  /** Contact emails */
  emails: z.array(z.string()).default([]),
  /** Raw WHOIS response */
  rawData: z.string().optional(),
});

export type WHOISData = z.infer<typeof whoisDataSchema>;

/**
 * Discovered subdomain information
 */
export const subdomainSchema = z.object({
  /** Subdomain name */
  name: z.string(),
  /** Resolved IP addresses */
  ips: z.array(z.string()).default([]),
  /** Status: live|dead|unknown */
  status: z.enum(['live', 'dead', 'unknown']).default('unknown'),
  /** DNS records */
  dnsRecords: dnsRecordsSchema.optional(),
  /** Cloud provider if detected */
  cloudProvider: z.string().optional(),
  /** CDN provider if detected */
  cdnProvider: z.string().optional(),
  /** Discovery source (subfinder, etc.) */
  discoveredVia: z.string(),
  /** Timestamp when subdomain was discovered */
  discoveredAt: z.date().default(() => new Date()),
  /** Open ports discovered */
  openPorts: z.array(portScanResultSchema).default([]),
  /** Total ports scanned */
  totalPortsScanned: z.number().int().default(0),
  /** Count of open ports */
  openPortsCount: z.number().int().default(0),
  /** Associated services */
  services: z.array(z.any()).optional(),
});

export type Subdomain = z.infer<typeof subdomainSchema>;

/**
 * Complete domain intelligence
 */
export const domainInfoSchema = z.object({
  /** Root domain being analyzed */
  rootDomain: z.string(),
  /** Discovered subdomains */
  subdomains: z.array(subdomainSchema).default([]),
  /** Root domain DNS records */
  dnsRecords: dnsRecordsSchema.optional(),
  /** WHOIS data */
  whois: whoisDataSchema.optional(),
  /** Total discovered subdomains */
  totalSubdomains: z.number().int().default(0),
  /** Live/responsive subdomains */
  liveSubdomains: z.number().int().default(0),
});

export type DomainInfo = z.infer<typeof domainInfoSchema>;
