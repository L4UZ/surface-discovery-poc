/**
 * Service-related data models and schemas
 */

import { z } from 'zod';

/**
 * HTTP security headers analysis
 */
export const securityHeadersSchema = z.object({
  /** Content Security Policy header */
  contentSecurityPolicy: z.string().optional(),
  /** HTTP Strict Transport Security */
  strictTransportSecurity: z.string().optional(),
  /** X-Frame-Options header */
  xFrameOptions: z.string().optional(),
  /** X-Content-Type-Options header */
  xContentTypeOptions: z.string().optional(),
  /** X-XSS-Protection header */
  xXssProtection: z.string().optional(),
  /** Referrer-Policy header */
  referrerPolicy: z.string().optional(),
  /** Permissions-Policy header */
  permissionsPolicy: z.string().optional(),
});

export type SecurityHeaders = z.infer<typeof securityHeadersSchema>;

/**
 * TLS/SSL certificate information
 */
export const tlsInfoSchema = z.object({
  /** TLS protocol version */
  version: z.string().optional(),
  /** Cipher suite */
  cipher: z.string().optional(),
  /** Certificate issuer */
  issuer: z.string().optional(),
  /** Certificate subject */
  subject: z.string().optional(),
  /** Certificate valid from date */
  validFrom: z.date().optional(),
  /** Certificate valid until date */
  validTo: z.date().optional(),
  /** Subject Alternative Names */
  san: z.array(z.string()).default([]),
  /** Whether certificate is expired */
  expired: z.boolean().default(false),
  /** Whether certificate is self-signed */
  selfSigned: z.boolean().default(false),
});

export type TLSInfo = z.infer<typeof tlsInfoSchema>;

/**
 * Detected technology/framework
 */
export const technologySchema = z.object({
  /** Technology name */
  name: z.string(),
  /** Version if detected */
  version: z.string().optional(),
  /** Category: web_server|framework|cms|library|etc */
  category: z.string(),
  /** Detection confidence (0.0 - 1.0) */
  confidence: z.number().min(0.0).max(1.0).default(1.0),
  /** Detection sources: headers|cookies|meta|javascript|etc */
  detectedFrom: z.array(z.string()).default([]),
});

export type Technology = z.infer<typeof technologySchema>;

/**
 * Live web service information
 */
export const serviceSchema = z.object({
  /** Service URL */
  url: z.string().url(),
  /** HTTP status code */
  statusCode: z.number().int().min(100).max(599),
  /** Response size in bytes */
  contentLength: z.number().int().nonnegative().optional(),
  /** Page title */
  title: z.string().optional(),
  /** Server header value */
  server: z.string().optional(),
  /** Detected technologies */
  technologies: z.array(technologySchema).default([]),
  /** Security headers analysis */
  securityHeaders: securityHeadersSchema.optional(),
  /** TLS/SSL information */
  tlsInfo: tlsInfoSchema.optional(),
  /** Response time in milliseconds */
  responseTime: z.number().nonnegative().optional(),
  /** Final URL after redirects */
  redirectsTo: z.string().url().optional(),
  /** Timestamp when service was discovered */
  discoveredAt: z.date().default(() => new Date()),
});

export type Service = z.infer<typeof serviceSchema>;
